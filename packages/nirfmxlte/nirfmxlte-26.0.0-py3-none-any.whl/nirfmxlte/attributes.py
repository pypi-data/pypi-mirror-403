"""attributes.py - Contains the ID of all attributes belongs to the module."""

from enum import Enum


class AttributeID(Enum):
    """This enum class contains the ID of all attributes belongs to the module."""

    SELECTED_PORTS = 3149821
    r"""Specifies the instrument port to be configured to acquire a signal. Use
    :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
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
    
    **Default values**
    
    +---------------------+-------------------+
    | Name (value)        | Description       |
    +=====================+===================+
    | PXIe-5830/5831/5832 | if1               |
    +---------------------+-------------------+
    | Other devices       | "" (empty string) |
    +---------------------+-------------------+
    """

    CENTER_FREQUENCY = 3145729
    r"""Specifies the center frequency of the acquired RF signal for a single carrier.
    
    For intra-band carrier aggregation, this attribute specifies the reference frequency of the subblock. This
    value is expressed in Hz.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value of this attribute is hardware dependent.
    """

    REFERENCE_LEVEL = 3145730
    r"""Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
    configured in dBm for RF devices and as Vpk-pk for baseband devices.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    EXTERNAL_ATTENUATION = 3145731
    r"""Specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer. This value is
    expressed in dB. Refer to the RF Attenuation and Signal Levels topic for your device in the *NI RF Vector Signal
    Analyzers Help* for more information about attenuation.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    REFERENCE_LEVEL_HEADROOM = 3149820
    r"""Specifies the margin RFmx adds to the :py:attr:`~nirfmxlte.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
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

    TRIGGER_TYPE = 3145732
    r"""Specifies the trigger type.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **None**.
    
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)      | Description                                                                                                              |
    +===================+==========================================================================================================================+
    | None (0)          | No Reference Trigger is configured.                                                                                      |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Digital Edge (1)  | The Reference Trigger is not asserted until a digital edge is detected. The source of the digital edge is specified      |
    |                   | using the Digital Edge Source attribute.                                                                                 |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | IQ Power Edge (2) | The Reference Trigger is asserted when the signal changes past the level specified by the slope (rising or falling),     |
    |                   | which is configured using the IQ Power Edge Slope attribute.                                                             |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Software (3)      | The Reference Trigger is not asserted until a software trigger occurs.                                                   |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    DIGITAL_EDGE_TRIGGER_SOURCE = 3145733
    r"""Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    DIGITAL_EDGE_TRIGGER_EDGE = 3145734
    r"""Specifies the active edge for the trigger. This attribute is used only when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.
    
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

    IQ_POWER_EDGE_TRIGGER_SOURCE = 3145735
    r"""Specifies the channel from which the device monitors the trigger. This attribute is used only when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    IQ_POWER_EDGE_TRIGGER_LEVEL = 3145736
    r"""Specifies the power level at which the device triggers. This value is expressed in dB when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm when
    you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
    the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
    used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE = 3149823
    r"""Specifies the reference for the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
    IQ Power Edge Level Type attribute is used only when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
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

    IQ_POWER_EDGE_TRIGGER_SLOPE = 3145737
    r"""Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
    asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
    used only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
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

    TRIGGER_DELAY = 3145738
    r"""Specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
    acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    TRIGGER_MINIMUM_QUIET_TIME_MODE = 3145739
    r"""Specifies whether the measurement computes the minimum quiet time used for triggering.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Auto**.
    
    +--------------+---------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                 |
    +==============+=============================================================================================+
    | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time attribute. |
    +--------------+---------------------------------------------------------------------------------------------+
    | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                        |
    +--------------+---------------------------------------------------------------------------------------------+
    """

    TRIGGER_MINIMUM_QUIET_TIME_DURATION = 3145740
    r"""Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
    trigger. This value is expressed in seconds.
    
    If you set the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising
    Slope**, the signal is quiet below the trigger level. If you set the IQ Power Edge Slope attribute to **Falling
    Slope**, the signal is quiet above the trigger level.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    LINK_DIRECTION = 3145769
    r"""Specifies the link direction of the received signal.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Uplink**.
    
    +--------------+---------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                           |
    +==============+=======================================================================================+
    | Downlink (0) | The measurement uses 3GPP LTE downlink specification to measure the received signal.  |
    +--------------+---------------------------------------------------------------------------------------+
    | Uplink (1)   | The measurement uses 3GPP LTE uplink specification to measure the received signal.    |
    +--------------+---------------------------------------------------------------------------------------+
    | Sidelink (2) | The measurement uses 3GPP LTE sidelink specifications to measure the received signal. |
    +--------------+---------------------------------------------------------------------------------------+
    """

    DUPLEX_SCHEME = 3145741
    r"""Specifies the duplexing technique of the signal being measured.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **FDD**.
    
    +--------------+-------------------------------------------------------------------------+
    | Name (Value) | Description                                                             |
    +==============+=========================================================================+
    | FDD (0)      | Specifies that the duplexing technique is frequency-division duplexing. |
    +--------------+-------------------------------------------------------------------------+
    | TDD (1)      | Specifies that the duplexing technique is time-division duplexing.      |
    +--------------+-------------------------------------------------------------------------+
    | LAA (2)      | Specifies that the duplexing technique is license assisted access.      |
    +--------------+-------------------------------------------------------------------------+
    """

    UPLINK_DOWNLINK_CONFIGURATION = 3145742
    r"""Specifies the configuration of the LTE frame structure in the time division duplex (TDD) mode. Refer to table 4.2-2 of
    the *3GPP TS 36.211* specification to configure the LTE frame.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **0**.
    
    +--------------+---------------------------------------------------------------------------+
    | Name (Value) | Description                                                               |
    +==============+===========================================================================+
    | 0 (0)        | The configuration of the LTE frame structure in the TDD duplex mode is 0. |
    +--------------+---------------------------------------------------------------------------+
    | 1 (1)        | The configuration of the LTE frame structure in the TDD duplex mode is 1. |
    +--------------+---------------------------------------------------------------------------+
    | 2 (2)        | The configuration of the LTE frame structure in the TDD duplex mode is 2. |
    +--------------+---------------------------------------------------------------------------+
    | 3 (3)        | The configuration of the LTE frame structure in the TDD duplex mode is 3. |
    +--------------+---------------------------------------------------------------------------+
    | 4 (4)        | The configuration of the LTE frame structure in the TDD duplex mode is 4. |
    +--------------+---------------------------------------------------------------------------+
    | 5 (5)        | The configuration of the LTE frame structure in the TDD duplex mode is 5. |
    +--------------+---------------------------------------------------------------------------+
    | 6 (6)        | The configuration of the LTE frame structure in the TDD duplex mode is 6. |
    +--------------+---------------------------------------------------------------------------+
    """

    ENODEB_CATEGORY = 3145808
    r"""Specifies the downlink eNodeB (Base station) category. Refer to the *3GPP 36.141* specification for more details.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Wide Area Base Station - Category A**.
    
    +--------------------------------------------------+------------------------------------------------------------------+
    | Name (Value)                                     | Description                                                      |
    +==================================================+==================================================================+
    | Wide Area Base Station - Category A (0)          | Specifies eNodeB is Wide Area Base Station - Category A.         |
    +--------------------------------------------------+------------------------------------------------------------------+
    | Wide Area Base Station - Category B Option 1 (1) | Specifies eNodeB is Wide Area Base Station - Category B Option1. |
    +--------------------------------------------------+------------------------------------------------------------------+
    | Wide Area Base Station - Category B Option 2 (2) | Specifies eNodeB is Wide Area Base Station - Category B Option2. |
    +--------------------------------------------------+------------------------------------------------------------------+
    | Local Area Base Station (3)                      | Specifies eNodeB is Local Area Base Station.                     |
    +--------------------------------------------------+------------------------------------------------------------------+
    | Home Base Station (4)                            | Specifies eNodeB is Home Base Station.                           |
    +--------------------------------------------------+------------------------------------------------------------------+
    | Medium Range Base Station (5)                    | Specifies eNodeB is Medium Range Base Station.                   |
    +--------------------------------------------------+------------------------------------------------------------------+
    """

    SPECIAL_SUBFRAME_CONFIGURATION = 3145770
    r"""Specifies the special subframe configuration index. It defines the length of DwPTS, GP, and UpPTS for TDD transmission
    as defined in the section 4.2 of *3GPP 36.211* specification.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0. Valid values are 0 to 9, inclusive.
    """

    NUMBER_OF_DUT_ANTENNAS = 3145771
    r"""Specifies the number of physical antennas available at the DUT for transmission in a MIMO setup.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1. Valid values are 1, 2, and 4.
    """

    TRANSMIT_ANTENNA_TO_ANALYZE = 3145772
    r"""Specifies the physical antenna connected to the analyzer.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0. Valid values are from 0 to N-1, where N is the number of DUT antennas.
    """

    NUMBER_OF_SUBBLOCKS = 3145763
    r"""Specifies the number of subblocks that are configured in intra-band non-contiguous carrier aggregation.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1. Set this attribute to 1 for single carrier and intra-band contiguous carrier
    aggregation.
    """

    SUBBLOCK_FREQUENCY = 3145817
    r"""Specifies the offset of the subblock from the center frequency. This value is expressed in Hz.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    BAND = 3145751
    r"""Specifies the evolved universal terrestrial radio access (E-UTRA) operating frequency band of a subblock, as defined in
    section 5.2 of the *3GPP TS 36.521* specification.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is 1. Valid values are from 1 to 256, inclusive.
    """

    COMPONENT_CARRIER_SPACING_TYPE = 3145747
    r"""Specifies the spacing between two adjacent component carriers within a subblock. Refer to the `Channel Spacing
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/channel-spacing.html>`_ and `Carrier Frequency Offset Definition and
    Reference Frequency
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_ topics for
    more information about component carrier spacing.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is **Nominal**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Nominal (0)  | Calculates the frequency spacing between component carriers, as defined in section 5.4.1A in the 3GPP TS 36.521          |
    |              | specification,                                                                                                           |
    |              | and sets the CC Freq attribute.                                                                                          |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Minimum (1)  | Calculates the frequency spacing between component carriers, as defined in section 5.4.1A of the 3GPP TS 36.521          |
    |              | specification, and sets the CC Freq attribute.                                                                           |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | User (2)     | The CC frequency that you configure in the CC Freq attribute is used.                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    COMPONENT_CARRIER_AT_CENTER_FREQUENCY = 3145748
    r"""Specifies the index of the component carrier having its center at the user-configured center frequency. RFmx LTE uses
    this attribute along with :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
    calculate the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`.
    
    Refer to the `Carrier Frequency Offset Definition and Reference Frequency
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/carrier-frequency-offset-definition-and-refer.html>`_  topic for
    more information about component carrier frequency.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    Valid values are -1, 0, 1 ... *n* - 1, inclusive, where *n* is the number of component carriers in the
    subblock.
    
    The default value is -1. If the value is -1, the component carrier frequency values are calculated such that
    the center of aggregated carriers (subblock) lies at the Center Frequency. This attribute is ignored if you set the CC
    Spacing Type attribute to **User**.
    """

    NUMBER_OF_COMPONENT_CARRIERS = 3145743
    r"""Specifies the number of component carriers configured within a subblock.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is 1.
    """

    COMPONENT_CARRIER_BANDWIDTH = 3145744
    r"""Specifies the channel bandwidth of the signal being measured. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **10 MHz**.
    """

    COMPONENT_CARRIER_FREQUENCY = 3145745
    r"""Specifies the offset of the component carrier from the subblock center frequency that you configure in the
    :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz. This attribute
    is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
    **User**.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    CELL_ID = 3145746
    r"""Specifies a physical layer cell identity.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are 0 to 503, inclusive.
    """

    CYCLIC_PREFIX_MODE = 3145749
    r"""Specifies the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Normal**.
    
    +--------------+----------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                      |
    +==============+==================================================================================+
    | Normal (0)   | The CP duration is 4.67 microseconds, and the number of symbols in a slot is 7.  |
    +--------------+----------------------------------------------------------------------------------+
    | Extended (1) | The CP duration is 16.67 microseconds, and the number of symbols in a slot is 6. |
    +--------------+----------------------------------------------------------------------------------+
    """

    DOWNLINK_AUTO_CELL_ID_DETECTION_ENABLED = 3145788
    r"""Specifies whether to enable autodetection of the cell ID. If the signal being measured does not contain primary and
    secondary sync signal (PSS/SSS), autodetection of cell ID is not possible. Detected cell ID can be fetched using
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_DOWNLINK_DETECTED_CELL_ID` attribute.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+-------------------------------------------------+
    | Name (Value) | Description                                     |
    +==============+=================================================+
    | False (0)    | The measurement uses the cell ID you configure. |
    +--------------+-------------------------------------------------+
    | True (1)     | The measurement auto detects the cell ID.       |
    +--------------+-------------------------------------------------+
    """

    DOWNLINK_CHANNEL_CONFIGURATION_MODE = 3145789
    r"""Specifies the channel configuration mode.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Test Model**.
    
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)     | Description                                                                                                              |
    +==================+==========================================================================================================================+
    | User Defined (1) | You have to manually set all the signals and channels.                                                                   |
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Test Model (2)   | You need to select a test model using the DL Test Model attribute, which will configure all the signals and channels     |
    |                  | automatically according to the 3GPP specification.                                                                       |
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    AUTO_PDSCH_CHANNEL_DETECTION_ENABLED = 3162196
    r"""Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_RESOURCE_BLOCK_ALLOCATION`
    attribute, the corresponding :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_CW0_MODULATION_TYPE` attribute, and the
    :py:attr:`~nirfmxlte.attributes.AttributeID.PDSCH_POWER` attribute are auto-detected by the measurement or
    user-specified. This attribute is not valid, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
    measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement uses the values of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation   |
    |              | Type, and the PDSCH Power attribute that you specify.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the values of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation   |
    |              | Type, and the PDSCH Power attribute that are auto-detected.                                                              |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    AUTO_CONTROL_CHANNEL_POWER_DETECTION_ENABLED = 3162197
    r"""Specifies whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PSS_POWER`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SSS_POWER`, :py:attr:`~nirfmxlte.attributes.AttributeID.PBCH_POWER`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.PDCCH_POWER`, and :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_POWER`
    attributes are auto-detected by the measurement or user-specified. Currently, auto-detection of
    :py:attr:`~nirfmxlte.attributes.AttributeID.PHICH_POWER` attribute is not supported. This attribute is not valid, when
    you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test
    Model**. The measurement ignores this attribute, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, PHICH Power, and PCFICH Power attributes that you        |
    |              | specify are used for the measurement.                                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, and PCFICH Power attributes are auto-detected and used   |
    |              | for the measurement.                                                                                                     |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    AUTO_PCFICH_CFI_DETECTION_ENABLED = 3162198
    r"""Specifies whether the value of :py:attr:`~nirfmxlte.attributes.AttributeID.PCFICH_CFI` attribute is auto-detected by
    the measurement or user-specified. This attribute is not valid, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
    measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The value of PCFICH CFI attribute used for the measurement is specified by you.                                          |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The value of PCFICH CFI attribute used for the measurement is auto-detected. This value is obtained by decoding the      |
    |              | PCFICH channel.                                                                                                          |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MI_CONFIGURATION = 3145811
    r"""Specifies whether the Mi parameter is specified by section 6.1.2.6 of *3GPP TS 36.141* specification for testing E-TMs
    or in the Table 6.9-1 of *3GPP TS 36.211* specification.
    The Mi parameter determines the number of PHICH groups in each downlink subframe, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute to **TDD**.
    
    This attribute is not valid, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. The
    measurement ignores this attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Standard**.
    
    +----------------+-------------------------------------------------------------------------------------------+
    | Name (Value)   | Description                                                                               |
    +================+===========================================================================================+
    | Test Model (0) | Mi parameter is set to 1 as specified in section 6.1.2.6 of 3GPP TS 36.141 specification. |
    +----------------+-------------------------------------------------------------------------------------------+
    | Standard (1)   | Mi parameter is specified by the Table 6.9-1 of 3GPP TS 36.211 specification.             |
    +----------------+-------------------------------------------------------------------------------------------+
    """

    DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO = 3145790
    r"""Specifies the ratio Rho\ :sub:`b`\/Rho\ :sub:`a`\ for the cell-specific ratio of one, two,
    or four cell-specific antenna ports as described in Table 5.2-1 in section 5.2 of the *3GPP TS 36.213*
    specification. This attribute determines the power of the channel resource element (RE) in the symbols that do not
    contain the reference symbols.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **P_B=0**.
    
    +--------------+--------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                          |
    +==============+======================================================================================+
    | P_B=0 (0)    | Specifies a ratio of 1 for one antenna port and 5/4 for two or four antenna ports.   |
    +--------------+--------------------------------------------------------------------------------------+
    | P_B=1 (1)    | Specifies a ratio of 4/5 for one antenna port and 1 for two or four antenna ports.   |
    +--------------+--------------------------------------------------------------------------------------+
    | P_B=2 (2)    | Specifies a ratio of 3/5 for one antenna port and 3/4 for two or four antenna ports. |
    +--------------+--------------------------------------------------------------------------------------+
    | P_B=3 (3)    | Specifies a ratio of 2/5 for one antenna port and 1/2 for two or four antenna ports. |
    +--------------+--------------------------------------------------------------------------------------+
    """

    PSS_POWER = 3145791
    r"""Specifies the power of primary synchronization signal (PSS) relative to the power of cell-specific reference signal.
    This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    SSS_POWER = 3145792
    r"""Specifies the power of secondary synchronization signal (SSS) relative to the power of cell-specific reference signal.
    This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    PBCH_POWER = 3145793
    r"""Specifies the power of physical broadcast channel (PBCH) relative to the power of cell-specific reference signal. This
    value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    PDCCH_POWER = 3145794
    r"""Specifies the power of physical downlink control channel (PDCCH) relative to the power of cell-specific reference
    signal. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    DOWNLINK_NUMBER_OF_SUBFRAMES = 3145795
    r"""Specifies the number of unique subframes transmitted by the DUT. If you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**, this
    attribute will be set to 10 for FDD and 20 for TDD by default.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 10. Valid values are 10 and 20.
    """

    PCFICH_CFI = 3145796
    r"""Specifies the control format indicator (CFI) carried by physical control format indicator channel (PCFICH). CFI is used
    to compute the number of OFDM symbols which will determine the size of physical downlink control channel (PDCCH) within
    a subframe.
    
    Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
    selector string to configure or read this attribute.
    
    The default value is 1.
    """

    PCFICH_POWER = 3145797
    r"""Specifies the power of physical control format indicator channel (PCFICH) relative to the power of cell-specific
    reference signal. This value is expressed in dB.
    
    Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
    selector string to configure or read this attribute.
    
    The default value is 0.
    """

    PHICH_RESOURCE = 3145798
    r"""Specifies the physical channel hybridARQ indicator channel (PHICH) resource value. This value is expressed in Ng. This
    attribute is used to calculate number of PHICH resource groups. Refer to section 6.9 of the *3GPP 36.211* specification
    for more information about PHICH.
    
    Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
    selector string to configure or read this attribute.
    
    The default value is **1/6**.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | 1/6 (0)      | Specifies the PHICH resource value is 1/6. |
    +--------------+--------------------------------------------+
    | 1/2 (1)      | Specifies the PHICH resource value is 1/2. |
    +--------------+--------------------------------------------+
    | 1 (2)        | Specifies the PHICH resource value is 1.   |
    +--------------+--------------------------------------------+
    | 2 (3)        | Specifies the PHICH resource value is 2.   |
    +--------------+--------------------------------------------+
    """

    PHICH_DURATION = 3145799
    r"""Specifies the physical hybrid-ARQ indicator channel (PHICH) duration.
    
    Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
    selector string to configure or read this attribute.
    
    The default value is **Normal**.
    
    +--------------+------------------------------------------------------------+
    | Name (Value) | Description                                                |
    +==============+============================================================+
    | Normal (0)   | Orthogonal sequences of length 4 is used to extract PHICH. |
    +--------------+------------------------------------------------------------+
    """

    PHICH_POWER = 3145800
    r"""Specifies the power of all BPSK symbols in a physical hybrid-ARQ indicator channel (PHICH) sequence. This value is
    expressed in dB.
    
    Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
    selector string to configure or read this attribute.
    
    The default value is 0.
    """

    NUMBER_OF_PDSCH_CHANNELS = 3145801
    r"""Specifies the number of physical downlink shared channel (PDSCH) allocations in a subframe.
    
    Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
    selector string to configure or read this attribute.
    
    The default value is 1. Valid values are 0 to 100, inclusive.
    """

    PDSCH_CW0_MODULATION_TYPE = 3145802
    r"""Specifies the modulation type of codeword0 PDSCH allocation.
    
    Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>" as the selector string to configure or read this attribute.
    
    The default value is **QPSK**.
    
    +--------------+-----------------------------------------+
    | Name (Value) | Description                             |
    +==============+=========================================+
    | QPSK (0)     | Specifies a QPSK modulation scheme.     |
    +--------------+-----------------------------------------+
    | 16 QAM (1)   | Specifies a 16-QAM modulation scheme.   |
    +--------------+-----------------------------------------+
    | 64 QAM (2)   | Specifies a 64-QAM modulation scheme.   |
    +--------------+-----------------------------------------+
    | 256 QAM (3)  | Specifies a 256-QAM modulation scheme.  |
    +--------------+-----------------------------------------+
    | 1024 QAM (4) | Specifies a 1024-QAM modulation scheme. |
    +--------------+-----------------------------------------+
    """

    PDSCH_RESOURCE_BLOCK_ALLOCATION = 3145803
    r"""Specifies the resource blocks of the physical downlink shared channel (PDSCH) allocation.
    
    The following string formats are supported for this property:
    
    1) *RB*
    \ :sub:`StartValue1`\-*RB*
    \ :sub:`StopValue1`\,*RB*
    \ :sub:`StartValue2`\-*RB*
    \ :sub:`StopValue2`\
    
    2) *RB*
    \ :sub:`1`\,*RB*
    \ :sub:`2`\
    
    3) *RB*
    \ :sub:`StartValue1`\-*RB*
    \ :sub:`StopValue1`\, *RB*
    \ :sub:`1`\,*RB*
    \ :sub:`StartValue2`\-*RB*
    \ :sub:`StopValue2`\,*RB*
    \ :sub:`2`\
    
    For example: If the RB allocation is 0-5,7,8,10-15, the RB allocation string specifies contiguous resource
    blocks from 0 to 5, resource block 7, resource block 8, and contiguous resource blocks from 10 to 15.
    
    Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>"
    as the selector string to configure or read this attribute.
    
    The default value is 0-49.
    """

    PDSCH_POWER = 3145804
    r"""Specifies the physical downlink shared channel (PDSCH) power level (Ra) relative to the power of the cell-specific
    reference signal. This value is expressed in dB. Measurement uses the
    :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_USER_DEFINED_CELL_SPECIFIC_RATIO` attribute to calculate the Rb.
    Refer to section 3.3 of the *3GPP 36.521* specification for more information about Ra.
    
    Use "PDSCH<*m*>" or "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/subframe<*l*>/PDSCH<*m*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    DOWNLINK_TEST_MODEL = 3145805
    r"""Specifies the E-UTRA test model type when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
    section 6.1.1 of the *3GPP 36.141* specification for more information regarding test model configurations.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **TM1.1**.
    
    +--------------+--------------------------------------+
    | Name (Value) | Description                          |
    +==============+======================================+
    | TM1.1 (0)    | Specifies an E-UTRA Test Model 1.1.  |
    +--------------+--------------------------------------+
    | TM1.2 (1)    | Specifies an E-UTRA Test Model 1.2.  |
    +--------------+--------------------------------------+
    | TM2 (2)      | Specifies an E-UTRA Test Model 2.    |
    +--------------+--------------------------------------+
    | TM2a (3)     | Specifies an E-UTRA Test Model 2a.   |
    +--------------+--------------------------------------+
    | TM2b (8)     | Specifies an E-UTRA Test Model 2b.   |
    +--------------+--------------------------------------+
    | TM3.1 (4)    | Specifies an E-UTRA Test Model 3.1.  |
    +--------------+--------------------------------------+
    | TM3.1a (7)   | Specifies an E-UTRA Test Model 3.1a. |
    +--------------+--------------------------------------+
    | TM3.1b (9)   | Specifies an E-UTRA Test Model 3.1b. |
    +--------------+--------------------------------------+
    | TM3.2 (5)    | Specifies an E-UTRA Test Model 3.2.  |
    +--------------+--------------------------------------+
    | TM3.3 (6)    | Specifies an E-UTRA Test Model 3.3.  |
    +--------------+--------------------------------------+
    """

    AUTO_RESOURCE_BLOCK_DETECTION_ENABLED = 3145766
    r"""Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_MODULATION_TYPE`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET`, and
    :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attributes are auto-detected by the
    measurement or if you specify the values of these attributes.
    
    The measurement ignores this attribute, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The values of the PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes that you specify     |
    |              | are used for the measurement.                                                                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The values of the PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes are detected         |
    |              | automatically and used for the measurement.                                                                              |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    AUTO_DMRS_DETECTION_ENABLED = 3145768
    r"""Specifies whether you configure the values of the demodulation reference signal (DMRS) parameters, such as
    :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_GROUP_HOPPING_ENABLED`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.UPLINK_SEQUENCE_HOPPING_ENABLED`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.CELL_ID`, :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_1`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_2`, and
    :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_DELTA_SEQUENCE_SHIFT` properties, or if the values of these
    attributes are auto-detected by the measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The user-specified DMRS parameters are used.                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The values of the DMRS parameters are automatically detected. Measurement returns an error if you set the ModAcc Sync    |
    |              | Mode attribute to Frame, since it is not possible to get the frame boundary when RFmx detects DMRS parameters            |
    |              | automatically.                                                                                                           |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    UPLINK_GROUP_HOPPING_ENABLED = 3145753
    r"""Specifies whether the sequence group number hopping for demodulation reference signal (DMRS) is enabled, as defined in
    section 5.5.1.3 of the *3GPP TS 36.211* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is **False**.
    
    +--------------+---------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                         |
    +==============+=====================================================================================================================+
    | False (0)    | The measurement uses zero as the sequence group number for all the slots.                                           |
    +--------------+---------------------------------------------------------------------------------------------------------------------+
    | True (1)     | Calculates the sequence group number for each slot, as defined in the section 5.5.1.3 of 3GPP 36.211 Specification. |
    +--------------+---------------------------------------------------------------------------------------------------------------------+
    """

    UPLINK_SEQUENCE_HOPPING_ENABLED = 3145754
    r"""Specifies whether the base sequence number hopping for the demodulation reference signal (DMRS) is enabled, as defined
    in section 5.5.1.3 of the *3GPP TS 36.211* specification.  This attribute is only valid only when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attribute to a value greater than 5.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                        |
    +==============+====================================================================================================================+
    | False (0)    | The measurement uses zero as the base sequence number for all the slots.                                           |
    +--------------+--------------------------------------------------------------------------------------------------------------------+
    | True (1)     | Calculates the base sequence number for each slot, as defined in the section 5.5.1.4 of 3GPP 36.211 specification. |
    +--------------+--------------------------------------------------------------------------------------------------------------------+
    """

    DMRS_OCC_ENABLED = 3145809
    r"""Specifies whether orthogonal cover codes (OCCs) need to be used on the demodulation reference signal (DMRS) signal. The
    measurement internally sets this attribute to **TRUE** for multi antenna cases.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement ignores the Cyclic Shift Field and uses the PUSCH n_DMRS_2 field for DMRS calculations.                  |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the table 5.5.2.1.1-1 of 3GPP 36.211 specification to decide the value of PUSCH n_DMRS_2 and [w(0)  |
    |              | w(1)] for DMRS signal based on the values you set for the Cyclic Shift Field and Tx Antenna to Analyze.                  |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    PUSCH_N_DMRS_1 = 3145759
    r"""Specifies the n_DMRS_1 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
    in a frame.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0. The valid values for this attribute are defined in table 5.5.2.1.1-2 of the *3GPP TS
    36.211* specification.
    """

    PUSCH_DELTA_SEQUENCE_SHIFT = 3145761
    r"""Specifies the physical uplink shared channel (PUSCH) delta sequence shift, which is used to calculate cyclic shift of
    the demodulation reference signal (DMRS). Refer to section 5.5.2.1.1 of the *3GPP TS 36.211* specification for more
    information about the PUSCH delta sequence shift.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    PUSCH_MODULATION_TYPE = 3145755
    r"""Specifies the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **QPSK**.
    
    +--------------+-----------------------------------------+
    | Name (Value) | Description                             |
    +==============+=========================================+
    | QPSK (0)     | Specifies a QPSK modulation scheme.     |
    +--------------+-----------------------------------------+
    | 16 QAM (1)   | Specifies a 16-QAM modulation scheme.   |
    +--------------+-----------------------------------------+
    | 64 QAM (2)   | Specifies a 64-QAM modulation scheme.   |
    +--------------+-----------------------------------------+
    | 256 QAM (3)  | Specifies a 256-QAM modulation scheme.  |
    +--------------+-----------------------------------------+
    | 1024 QAM (4) | Specifies a 1024-QAM modulation scheme. |
    +--------------+-----------------------------------------+
    """

    PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS = 3145756
    r"""Specifies the number of resource allocation clusters, with each cluster including one or more consecutive resource
    blocks. Refer to 5.5.2.1.1 of the *3GPP TS 36.213* specification for more information about the number of channels in
    the physical uplink shared channel (PUSCH).
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 1.
    """

    PUSCH_RESOURCE_BLOCK_OFFSET = 3145758
    r"""Specifies the starting resource block number of a physical uplink shared channel (PUSCH) cluster.
    
    Use "cluster<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"/cluster<*l*>"  as the selector string to
    configure or read this attribute.
    
    The default value is 0.
    """

    PUSCH_NUMBER_OF_RESOURCE_BLOCKS = 3145762
    r"""Specifies the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster.
    
    Use "cluster<*l*>" or "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"/cluster<*l*>"  as the selector string to
    configure or read this attribute.
    
    The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
    bandwidth are configured.
    """

    PUSCH_N_DMRS_2 = 3145760
    r"""Specifies the n_DMRS_2 value, which is used to calculate the cyclic shift of the demodulation reference signal (DMRS)
    in a slot. The valid values for this attribute are, as defined in table 5.5.2.1.1-1 of the *3GPP TS 36.211*
    specification.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    PUSCH_CYCLIC_SHIFT_FIELD = 3145810
    r"""Specifies the cyclic shift field in uplink-related DCI format. When the
    :py:attr:`~nirfmxlte.attributes.AttributeID.DMRS_OCC_ENABLED` attribute is set to **True**,
    the measurement uses the table 5.5.2.1.1-1 of *3GPP 36.211* specification to decide the valued of n(2)DMRS and
    [w(0) w(1)] for DMRS signal based on Cyclic Shift Field along with
    :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE`.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are 0 to 7, inclusive.
    """

    PUSCH_POWER = 3145767
    r"""Specifies the power of the physical uplink shared channel (PUSCH) data relative to PUSCH DMRS for a component carrier.
    This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    SRS_ENABLED = 3145773
    r"""Specifies whether the LTE signal getting measured contains SRS transmission.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is **False**.
    
    +--------------+------------------------------------------------------+
    | Name (Value) | Description                                          |
    +==============+======================================================+
    | False (0)    | Measurement expects signal without SRS transmission. |
    +--------------+------------------------------------------------------+
    | True (1)     | Measurement expects signal with SRS transmission.    |
    +--------------+------------------------------------------------------+
    """

    SRS_SUBFRAME_CONFIGURATION = 3145774
    r"""Specifies the SRS subframe configuration specified in the Table 5.5.3.3-1 of *3GPP 36.211* specification. It is a
    cell-specific attribute. This attribute defines the subframes that are reserved for SRS transmission in a given cell.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute
    to **FDD**, valid values are from 0 to 14, and when you set the Duplex Scheme attribute to **TDD**, valid values are
    from 0 to 13.
    """

    SRS_C_SRS = 3145775
    r"""Specifies the cell-specific SRS bandwidth configuration *C\ :sub:`SRS*
    `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 7. Valid values are from 0 to 7, inclusive.
    """

    SRS_B_SRS = 3145776
    r"""Specifies the UE specific SRS bandwidth configuration *B\ :sub:`SRS*
    `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are from 0 to 3, inclusive.
    """

    SRS_I_SRS = 3145777
    r"""Specifies the SRS configuration index *I\ :sub:`SRS*
    `\. It is used to determine the SRS periodicity and SRS subframe offset. It is a UE specific attribute which
    defines whether the SRS is transmitted in the subframe reserved for SRS by SRS subframe configuration. Refer to *3GPP
    36.213* specification for more details.
    
    If the periodicity of the given SRS configuration is more than one frame, use the multi-frame generation with a
    digital trigger at the start of the first frame for accurate demodulation.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.DUPLEX_SCHEME` attribute
    to **FDD**, valid values are from 0 to 636, and when you set the Duplex Scheme attribute to **TDD**, valid values are
    from 0 to 644.
    """

    SRS_N_RRC = 3145778
    r"""Specifies the SRS frequency domain position *n\ :sub:`RRC*
    `\. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are from 0 to 23, inclusive.
    """

    SRS_N_SRS_CS = 3145779
    r"""Specifies the cyclic shift value *n\ :sub:`SRS*
    \ :sup:`CS`\
    `\ used for generating SRS base sequence. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more
    details.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are from 0 to 7, inclusive.
    """

    SRS_B_HOP = 3145780
    r"""Specifies the SRS hopping bandwidth b\ :sub:`hop`\. Frequency hopping for SRS signal is enabled when the value of SRS
    b_hop attribute is less than the value of :py:attr:`~nirfmxlte.attributes.AttributeID.SRS_B_SRS` attribute.
    
    If the given measurement interval is more than one frame, use the multi-frame generation with digital trigger
    at the start of the first frame for accurate demodulation, since hopping pattern will vary across frames.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 3. Valid values are from 0 to 3, inclusive.
    """

    SRS_K_TC = 3145781
    r"""Specifies the transmission comb index. If you set this attribute to 0, SRS is transmitted on the even subcarriers in
    the allocated region. If you set this attribute to 1, SRS is transmitted on the odd subcarriers in the allocated
    region.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    SRS_MAXIMUM_UPPTS_ENABLED = 3145782
    r"""Specifies SRS MaxUpPTS parameter which determines whether SRS is transmitted in all possible RBs of UpPTS symbols in
    LTE TDD. Refer to section 5.5.3.2 of *3GPP 36.211* specification for more details.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is **False**.
    
    +--------------+-------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                               |
    +==============+===========================================================================================+
    | False (0)    | In special subframe, SRS is transmitted in RBs specified by SRS bandwidth configurations. |
    +--------------+-------------------------------------------------------------------------------------------+
    | True (1)     | In special subframe, SRS is transmitted in all possible RBs.                              |
    +--------------+-------------------------------------------------------------------------------------------+
    """

    SRS_SUBFRAME1_N_RA = 3145783
    r"""Specifies the number of format 4 PRACH allocations in UpPTS for Subframe 1, first special subframe, in LTE TDD.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are 0 to 6.
    """

    SRS_SUBFRAME6_N_RA = 3145784
    r"""Specifies the number of format 4 PRACH allocations in UpPTS for Subframe 6, second special subframe, in LTE TDD. It is
    ignored for UL/DL Configuration 3, 4, and 5.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are 0 to 6.
    """

    SRS_POWER = 3145785
    r"""Specifies the average power of SRS transmission with respect to PUSCH DMRS power. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    PSSCH_MODULATION_TYPE = 3145813
    r"""Specifies the modulation scheme used in physical sidelink shared channel (PSSCH) of the signal being measured.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is **QPSK**.
    
    +--------------+---------------------------------------+
    | Name (Value) | Description                           |
    +==============+=======================================+
    | QPSK (0)     | Specifies a QPSK modulation scheme.   |
    +--------------+---------------------------------------+
    | 16 QAM (1)   | Specifies a 16-QAM modulation scheme. |
    +--------------+---------------------------------------+
    | 64 QAM (2)   | Specifies a 64-QAM modulation scheme. |
    +--------------+---------------------------------------+
    """

    PSSCH_RESOURCE_BLOCK_OFFSET = 3145814
    r"""Specifies the starting resource block number of a physical sidelink shared channel (PSSCH) allocation.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    PSSCH_NUMBER_OF_RESOURCE_BLOCKS = 3145815
    r"""Specifies the number of consecutive resource blocks in a physical sidelink shared channel (PSSCH) allocation.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
    bandwidth are configured.
    """

    PSSCH_POWER = 3145816
    r"""Specifies the power of the physical sidelink shared channel (PSSCH) data relative to PSSCH DMRS for a component
    carrier. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    LAA_STARTING_SUBFRAME = 3162199
    r"""Specifies the starting subframe of an LAA burst.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    LAA_NUMBER_OF_SUBFRAMES = 3162200
    r"""Specifies the number of subframes in an LAA burst including the starting subframe.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 1.
    """

    LAA_UPLINK_START_POSITION = 3162201
    r"""Specifies the starting position of symbol 0 in the first subframe of an LAA uplink burst. Refer to section 5.6 of the
    *3GPP 36.211* specification for more information regarding LAA uplink start position.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **00**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | 00 (0)       | The symbol 0 in the first subframe of an LAA uplink burst is completely occupied. There is no idle duration.             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 01 (1)       | The starting position of symbol 0 in the first subframe of an LAA uplink burst is calculated as per section 5.6 (frame   |
    |              | structure type 3) of the 3GPP 36.211 specification. The symbol is partially occupied.                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 10 (2)       | The starting position of symbol 0 in the first subframe of an LAA uplink burst is calculated as per section 5.6 (frame   |
    |              | structure type 3) of the 3GPP 36.211 specification. The symbol is partially occupied.                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 11 (3)       | The symbol 0 in the first subframe of an LAA uplink burst is completely idle. Symbol 0 is not transmitted in this case.  |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    LAA_UPLINK_ENDING_SYMBOL = 3162202
    r"""Specifies the ending symbol number in the last subframe of an LAA uplink burst. Refer to section 5.3.3.1.1A of the
    *3GPP 36.212* specification for more information regarding LAA uplink ending symbol.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **13**.
    
    +--------------+-------------------------------------------------------------+
    | Name (Value) | Description                                                 |
    +==============+=============================================================+
    | 12 (12)      | The last subframe of an LAA uplink burst ends at symbol 12. |
    +--------------+-------------------------------------------------------------+
    | 13 (13)      | The last subframe of an LAA uplink burst ends at symbol 13. |
    +--------------+-------------------------------------------------------------+
    """

    LAA_DOWNLINK_STARTING_SYMBOL = 3162203
    r"""Specifies the starting symbol number in the first subframe of an LAA downlink burst. Refer to section 13A of the *3GPP
    36.213* specification for more information regarding LAA downlink starting symbol.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **0**.
    
    +--------------+-----------------------------------------------------------------+
    | Name (Value) | Description                                                     |
    +==============+=================================================================+
    | 0 (0)        | The first subframe of an LAA downlink burst starts at symbol 0. |
    +--------------+-----------------------------------------------------------------+
    | 7 (7)        | The first subframe of an LAA downlink burst starts at symbol 7. |
    +--------------+-----------------------------------------------------------------+
    """

    LAA_DOWNLINK_NUMBER_OF_ENDING_SYMBOLS = 3162204
    r"""Specifies the number of ending symbols in the last subframe of an LAA downlink burst. Refer to section 4.3 of the *3GPP
    36.211* specification for more information regarding LAA downlink number of ending symbols.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **14**.
    
    +--------------+-----------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                       |
    +==============+===================================================================================+
    | 3 (3)        | The number of ending symbols in the last subframe of an LAA downlink burst is 3.  |
    +--------------+-----------------------------------------------------------------------------------+
    | 6 (6)        | The number of ending symbols in the last subframe of an LAA downlink burst is 6.  |
    +--------------+-----------------------------------------------------------------------------------+
    | 9 (9)        | The number of ending symbols in the last subframe of an LAA downlink burst is 9.  |
    +--------------+-----------------------------------------------------------------------------------+
    | 10 (10)      | The number of ending symbols in the last subframe of an LAA downlink burst is 10. |
    +--------------+-----------------------------------------------------------------------------------+
    | 11 (11)      | The number of ending symbols in the last subframe of an LAA downlink burst is 11. |
    +--------------+-----------------------------------------------------------------------------------+
    | 12 (12)      | The number of ending symbols in the last subframe of an LAA downlink burst is 12. |
    +--------------+-----------------------------------------------------------------------------------+
    | 14 (14)      | The number of ending symbols in the last subframe of an LAA downlink burst is 14. |
    +--------------+-----------------------------------------------------------------------------------+
    """

    NCELL_ID = 3162206
    r"""Specifies the narrowband physical layer cell identity.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are 0 to 503, inclusive.
    """

    NB_IOT_UPLINK_SUBCARRIER_SPACING = 3162207
    r"""Specifies the subcarrier bandwidth of an NB-IoT signal. This attribute specifies the spacing between adjacent
    subcarriers.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **15 kHz**.
    
    +--------------+-------------------------------------+
    | Name (Value) | Description                         |
    +==============+=====================================+
    | 15 kHz (0)   | The subcarrier spacing is 15 kHz.   |
    +--------------+-------------------------------------+
    | 3.75 kHz (1) | The subcarrier spacing is 3.75 kHz. |
    +--------------+-------------------------------------+
    """

    AUTO_NPUSCH_CHANNEL_DETECTION_ENABLED = 3162208
    r"""Specifies whether the values of the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_TONE_OFFSET`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES`, and
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_MODULATION_TYPE` attributes are auto-detected by the measurement or
    specified by you.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement uses the values that you specify for the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod      |
    |              | Type attributes.                                                                                                         |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the values of the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod Type attributes that   |
    |              | are auto-detected.                                                                                                       |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    NPUSCH_FORMAT = 3162209
    r"""Specifies the NPUSCH format. A value of 1 indicates that narrowband physical uplink shared channel (NPUSCH) carries
    user data (UL-SCH) and a value of 2 indicates that NPUSCH carries uplink control information.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 1.
    """

    NPUSCH_STARTING_SLOT = 3162226
    r"""Specifies the starting slot number of the NPUSCH burst.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    NPUSCH_TONE_OFFSET = 3162210
    r"""Specifies the location of the starting subcarrier (tone) within the 200 kHz bandwidth that is allocated to the
    narrowband physical uplink shared channel (NPUSCH).
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    
    For 15 kHz subcarrier spacing, the valid values are as follows:
    
    - for 1 tones, 0 to 11, inclusive
    
    - for 3 tones, 0, 3, 6, and 9
    
    - for 6 tones, 0 and 6
    
    - for 12 tones, 0
    
    For 3.75 kHz subcarrier spacing, the valid values are 0 to 47, inclusive.
    """

    NPUSCH_NUMBER_OF_TONES = 3162211
    r"""Specifies the number of subcarriers (tones) within the 200 kHz bandwidth that is allocated to the narrowband physical
    uplink shared channel (NPUSCH).
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 1.
    
    For Format 1 and 15 kHz subcarrier spacing, the valid values are 1, 3, 6, and 12.
    
    For Format 1, 3.75 kHz subcarrier spacing, and Format 2, the valid value is 1.
    """

    NPUSCH_MODULATION_TYPE = 3162212
    r"""Specifies the modulation type that is used by the narrowband physical uplink shared channel (NPUSCH). This attribute is
    valid when :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` is equal to 1 and
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is equal to 1. The modulation type for other configurations
    is defined in Table 10.1.3.2-1 of the *3GPP TS 36.211* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is **BPSK**.
    
    +--------------+-------------------------------------+
    | Name (Value) | Description                         |
    +==============+=====================================+
    | BPSK (0)     | Specifies a BPSK modulation scheme. |
    +--------------+-------------------------------------+
    | QPSK (1)     | Specifies a QPSK modulation scheme. |
    +--------------+-------------------------------------+
    """

    NPUSCH_DMRS_BASE_SEQUENCE_MODE = 3162213
    r"""Specifies whether the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_INDEX` attribute is
    computed by the measurement or specified by you. This attribute is valid when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` attribute to 1, and the
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **Auto**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Manual (0)   | The measurement uses the value that you specify for the NPUSCH DMRS Base Sequence Index attribute.                       |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Auto (1)     | The measurement uses the value of NCell ID attribute to compute the NPUSCH DMRS Base Sequence Index as defined in        |
    |              | section 10.1.4.1.2 of the 3GPP TS 36.211 specification.                                                                  |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    NPUSCH_DMRS_BASE_SEQUENCE_INDEX = 3162214
    r"""Specifies the base sequence index of the Narrowband Physical Uplink Shared Channel (NPUSCH) DMRS as defined in section
    10.1.4.1.2 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **False**, the
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_BASE_SEQUENCE_MODE` attribute to **Manual**, and the
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3, 6, or 12.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    
    - For 3 tones, valid values are 0 to 11, inclusive.
    
    - For 6 tones, valid values are 0 to 13, inclusive.
    
    - For 12 tones, valid values are 0 to 29, inclusive.
    """

    NPUSCH_DMRS_CYCLIC_SHIFT = 3162215
    r"""Specifies the cyclic shift of the narrowband physical uplink shared channel (NPUSCH) DMRS as defined in Table
    10.1.4.1.2-3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 3 or 6. If the value of NPUSCH Num
    Tones attribute is 12, the NPUSCH DMRS Cyclic Shift attribute has a fixed value of 0.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    
    - For 3 tones, valid values are 0 to 2, inclusive.
    
    - For 6 tones, valid values are 0 to 3, inclusive.
    """

    NPUSCH_DMRS_GROUP_HOPPING_ENABLED = 3162217
    r"""Specifies whether the group hopping is enabled for narrowband physical uplink shared channel (NPUSCH) DMRS. This
    attribute is valid only when the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_FORMAT` is 1.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | Group hopping is disabled.                                                                                               |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | Group hopping is enabled. The sequence group number is calculated as defined in section 10.1.4.1.3 of the 3GPP TS        |
    |              | 36.211 specification.                                                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    NPUSCH_DMRS_DELTA_SEQUENCE_SHIFT = 3162216
    r"""Specifies the delta sequence shift of the narrowband physical uplink shared channel (NPUSCH) DMRS, which is used to
    calculate the sequence shift pattern. This value is used to compute the sequence group number as defined in section
    10.1.4.1.3 of the *3GPP TS 36.211* specification. This attribute is valid when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_DMRS_GROUP_HOPPING_ENABLED` attribute to **True**.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are 0 to 29, inclusive.
    """

    NB_IOT_DOWNLINK_CHANNEL_CONFIGURATION_MODE = 3162244
    r"""Specifies the downlink channel configuration mode for NB-IoT.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Test Model**.
    
    +------------------+--------------------------------------------------------------------------------------------------------------+
    | Name (Value)     | Description                                                                                                  |
    +==================+==============================================================================================================+
    | User Defined (1) | You have to manually set all the signals and channels.                                                       |
    +------------------+--------------------------------------------------------------------------------------------------------------+
    | Test Model (2)   | Configures all the signals and channels automatically according to the 3GPP NB-IoT test model specification. |
    +------------------+--------------------------------------------------------------------------------------------------------------+
    """

    NPSS_POWER = 3162247
    r"""Specifies the power of the NB-IoT primary synchronization signal (NPSS) relative to the power of the NB-IoT downlink
    reference signal (NRS). This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    NSSS_POWER = 3162249
    r"""Specifies the power of the NB-IoT secondary synchronization signal (NSSS) relative to the power of the NB-IoT downlink
    reference signal (NRS). This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    NPDSCH_POWER = 3162250
    r"""Specifies the NB-IoT physical downlink shared channel (NPDSCH) power level relative to the power of the NB-IoT downlink
    reference signal (NRS). This value is expressed in dB.
    
    Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
    selector string to configure or read this attribute.
    
    The default value is 0.
    """

    NPDSCH_ENABLED = 3162251
    r"""Specifies whether NPDSCH is active in a particular subframe. Note that in even-numbered frames, subframes 0, 5, and 9
    are reserved for NPBCH, NPSS, and NSSS. In odd-numbered frames, subframes 10 and 15 are reserved for NPBCH and NPSS.The
    measurement will return an error if you try to configure NPDSCH for those subframes.
    
    Use "subframe<*l*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/subframe<*l*>" as the
    selector string to configure or read this attribute.
    
    The default value is **False**.
    
    +--------------+-----------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                       |
    +==============+===================================================================================+
    | False (0)    | Indicates to the measurement that NPDSCH is not present in a particular subframe. |
    +--------------+-----------------------------------------------------------------------------------+
    | True (1)     | Indicates to the measurement that NPDSCH is present in a particular subframe.     |
    +--------------+-----------------------------------------------------------------------------------+
    """

    EMTC_ANALYSIS_ENABLED = 3162224
    r"""Specifies whether the component carrier contains enhanced machine type communications (Cat-M1 or Cat-M2) transmission.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is **False**.
    
    +--------------+-----------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                           |
    +==============+=======================================================================================================================+
    | False (0)    | The measurement considers the signal as LTE FDD/TDD transmission.                                                     |
    +--------------+-----------------------------------------------------------------------------------------------------------------------+
    | True (1)     | Detects the eMTC half duplex pattern, narrow band hopping, and eMTC guard symbols present in the uplink transmission. |
    +--------------+-----------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_MEASUREMENT_ENABLED = 3162112
    r"""Specifies whether to enable the ModAcc measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    MODACC_MULTICARRIER_FILTER_ENABLED = 3162114
    r"""Specifies whether to use a filter to suppress the interference from out of band emissions into the carriers being
    measured.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+-------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                           |
    +==============+=======================================================================================================+
    | False (0)    | The measurement does not use the multicarrier filter.                                                 |
    +--------------+-------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement filters out interference from out of band emissions into the carriers being measured. |
    +--------------+-------------------------------------------------------------------------------------------------------+
    """

    MODACC_MULTICARRIER_TIME_SYNCHRONIZATION_MODE = 3162238
    r"""Specifies the time synchronization mode used in uplink in the case of carrier aggregation.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Common**.
    
    +-----------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)    | Description                                                                                                              |
    +=================+==========================================================================================================================+
    | Common (0)      | Specifies that a common time synchronization value is used for synchronization of all the component carriers and time    |
    |                 | synchronization value is obtained from the synchronization of the first active component carrier of the first subblock.  |
    +-----------------+--------------------------------------------------------------------------------------------------------------------------+
    | Per Carrier (1) | Specifies that time synchronization is performed on each component carrier.                                              |
    +-----------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_SYNCHRONIZATION_MODE = 3162115
    r"""Specifies whether the measurement is performed from the frame or the slot boundary.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    Refer to the `LTE Modulation Accuracy
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about
    synchronization mode.
    
    The default value is **Slot**.
    
    .. note::
       When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, the measurement
       supports only **Frame** synchronization mode.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Frame (0)    | The frame boundary is detected, and the measurement is performed over the ModAcc Meas Length attribute, starting at the  |
    |              | ModAcc Meas Offset attribute from the frame boundary. When you set the Trigger Type attribute to Digital Edge, the       |
    |              | measurement expects a trigger at the frame boundary.                                                                     |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Slot (1)     | The slot boundary is detected, and the measurement is performed over the ModAcc Meas Length attribute starting at the    |
    |              | ModAcc Meas Offset attribute from the slot boundary. When you set the Trigger Type attribute to Digital Edge, the        |
    |              | measurement expects a trigger at any slot boundary.                                                                      |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Marker (2)   | The measurement expects a marker (trigger) at the frame boundary from the user. The measurement takes advantage of       |
    |              | triggered acquisitions to reduce processing resulting in faster measurement time. Measurement is performed over the      |
    |              | ModAcc Meas Length attribute starting at ModAcc Meas Offset attribute from the frame boundary.                           |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_MEASUREMENT_OFFSET = 3162116
    r"""Specifies the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
    by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. This value is expressed in
    slots.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0. For uplink, the upper limit is 19. For downlink, the upper limit is
    (2*:py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_NUMBER_OF_SUBFRAMES` - 1).
    """

    MODACC_MEASUREMENT_LENGTH = 3162117
    r"""Specifies the number of slots to be measured. This value is expressed in slots. For NB-IoT a measurement length of 20
    slots is recommended.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    MODACC_FREQUENCY_ERROR_ESTIMATION = 3203084
    r"""Specifies the operation mode of frequency error estimation.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Normal**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Normal (1)   | Estimate and correct frequency error of range +/- half subcarrier spacing.                                               |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Wide (2)     | Estimate and correct frequency error of range +/- half resource block when Auto RB Detection Enabled is True, or range   |
    |              | +/- number of guard subcarrier when Auto RB Detection Enabled is False.                                                  |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_IQ_ORIGIN_OFFSET_ESTIMATION_ENABLED = 3162233
    r"""Specifies whether to estimate IQ origin offset.
    
    .. note::
       IQ origin offset estimation is supported only when you set the
       :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Uplink** or **Sidelink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+---------------------------------------------------------+
    | Name (Value) | Description                                             |
    +==============+=========================================================+
    | False (0)    | IQ origin offset estimation and correction is disabled. |
    +--------------+---------------------------------------------------------+
    | True (1)     | IQ origin offset estimation and correction is enabled.  |
    +--------------+---------------------------------------------------------+
    """

    MODACC_IQ_MISMATCH_ESTIMATION_ENABLED = 3162234
    r"""Specifies whether to estimate IQ mismatch such as gain imbalance, quadrature skew, and timing skew.
    
    .. note::
       Timing skew value is estimated only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
       attribute to **Uplink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+-------------------------------------+
    | Name (Value) | Description                         |
    +==============+=====================================+
    | False (0)    | IQ mismatch estimation is disabled. |
    +--------------+-------------------------------------+
    | True (1)     | IQ mismatch estimation is enabled.  |
    +--------------+-------------------------------------+
    """

    MODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED = 3162235
    r"""Specifies whether to enable IQ gain imbalance correction.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+-------------------------------------------+
    | Name (Value) | Description                               |
    +==============+===========================================+
    | False (0)    | IQ gain imbalance correction is disabled. |
    +--------------+-------------------------------------------+
    | True (1)     | IQ gain imbalance correction is enabled.  |
    +--------------+-------------------------------------------+
    """

    MODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED = 3162236
    r"""Specifies whether to enable IQ quadrature error correction.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+---------------------------------------------+
    | Name (Value) | Description                                 |
    +==============+=============================================+
    | False (0)    | IQ quadrature error correction is disabled. |
    +--------------+---------------------------------------------+
    | True (1)     | IQ quadrature error correction is enabled.  |
    +--------------+---------------------------------------------+
    """

    MODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED = 3162237
    r"""Specifies whether to enable IQ timing skew correction.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+----------------------------------------+
    | Name (Value) | Description                            |
    +==============+========================================+
    | False (0)    | IQ timing skew correction is disabled. |
    +--------------+----------------------------------------+
    | True (1)     | IQ timing skew correction is enabled.  |
    +--------------+----------------------------------------+
    """

    MODACC_SPECTRUM_INVERTED = 3162166
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

    MODACC_CHANNEL_ESTIMATION_TYPE = 3162167
    r"""Specifies the method used for the channel estimation for the ModAcc measurement. The measurement ignores this
    attribute, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Reference+Data**.
    
    +--------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)       | Description                                                                                                              |
    +====================+==========================================================================================================================+
    | Reference (0)      | Only the demodulation reference signal (DMRS) symbol is used to calculate the channel coefficients.                      |
    +--------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Reference+Data (1) | Both the DMRS symbol and the data symbol are used to calculate the channel coefficients, as specified by the 3GPP        |
    |                    | 36.521 specification, Annexe E.                                                                                          |
    +--------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_EVM_UNIT = 3162118
    r"""Specifies the units of the EVM results.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Percentage**.
    
    +----------------+--------------------------------------+
    | Name (Value)   | Description                          |
    +================+======================================+
    | Percentage (0) | The EVM is reported as a percentage. |
    +----------------+--------------------------------------+
    | dB (1)         | The EVM is reported in dB.           |
    +----------------+--------------------------------------+
    """

    MODACC_FFT_WINDOW_TYPE = 3162168
    r"""Specifies the FFT window type used for the EVM calculation for the ModAcc measurement.
    
    Refer to the `LTE Modulation Accuracy
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about FFT window
    type.
    
    The default value is **Custom**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | 3GPP (0)     | The maximum EVM between the start window position and the end window position is returned according to the 3GPP          |
    |              | specification. The FFT window positions are specified by the                                                             |
    |              | attribute. Refer to the Annexe E.3.2 of 3GPP TS 36.521 specification for more information on the FFT window.             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Custom (1)   | Only one FFT window position is used for the EVM calculation. FFT window position is specified by ModAcc FFT Window      |
    |              | Offset attribute.                                                                                                        |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_FFT_WINDOW_OFFSET = 3162119
    r"""Specifies the position of the FFT window used to calculate the EVM. The offset is expressed as a percentage of the
    cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end of cyclic prefix. If you set
    this attribute to 100, the EVM window starts at the beginning of cyclic prefix.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 50. Valid values are 0 to 100, inclusive.
    """

    MODACC_FFT_WINDOW_LENGTH = 3162169
    r"""Specifies the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
    attribute is used when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
    **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
    Delta_C+W/2. Refer to the Annexe E.3.2 of *3GPP 36.521* specification for more information.
    
    Refer to the `LTE Modulation Accuracy
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-modulation-accuracy.html>`_ topic for more information about FFT Window
    Length.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is as given in the 3GPP specification. The default value is 91.7 %CP for 10M bandwidth. Valid
    values range from -1 to 100, inclusive.
    
    When this attribute is set to -1, RFmx populates the FFT Window Length based on carrier bandwidth
    automatically, as given in the Annexe E.5.1 of *3GPP 36.104* specification.
    """

    MODACC_COMMON_CLOCK_SOURCE_ENABLED = 3162121
    r"""Specifies whether the same Reference Clock is used for the local oscillator and the digital-to-analog converter in the
    transmitter. When the same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.
    
    The ModAcc measurement ignores this attribute, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------+
    | Name (Value) | Description                                                        |
    +==============+====================================================================+
    | False (0)    | The Sample Clock error is estimated independently.                 |
    +--------------+--------------------------------------------------------------------+
    | True (1)     | The Sample Clock error is estimated from carrier frequency offset. |
    +--------------+--------------------------------------------------------------------+
    """

    MODACC_EVM_WITH_EXCLUSION_PERIOD_ENABLED = 3162162
    r"""Specifies whether to exclude some portion of the slots when calculating the EVM. This attribute is valid only when
    there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP TS 36.521-1* specification for
    more information about exclusion.
    
    The measurement ignores this attribute, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | EVM is calculated on complete slots.                                                                                     |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | EVM is calculated on truncated slots. The power changes at the slot boundaries are detected by the measurement, and the  |
    |              | defined 3GPP specification period is excluded from the slots being measured.                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_SPECTRAL_FLATNESS_CONDITION = 3162120
    r"""Specifies the frequency ranges at which to measure spectral flatness. The measurement ignores this attribute, when you
    set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Normal**.
    
    +--------------+----------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                    |
    +==============+================================================================================================================+
    | Normal (0)   | Uses the frequency range defined in the section 6.5.2.4.5, and table 6.5.2.4.3-1 of 3GPP 36.521 specification. |
    +--------------+----------------------------------------------------------------------------------------------------------------+
    | Extreme (1)  | Uses the frequency range defined in the section 6.5.2.4.5, and table 6.5.2.4.3-2 of 3GPP 36.521 specification. |
    +--------------+----------------------------------------------------------------------------------------------------------------+
    """

    MODACC_IN_BAND_EMISSION_MASK_TYPE = 3162225
    r"""Specifies the in-band emissions mask type to be used for measuring in-band emission margin (dB) and subblock in-Band
    emission margin (dB) results.
    
    Refer to section 6.5.2.3.5 of the *3GPP 36.521-1* specification for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Release 8-10** for bandwidths other than 200 KHz and
    :py:attr:`~nirfmxlte.attributes.AttributeID.EMTC_ANALYSIS_ENABLED` is **False**. It is **Release 11 Onwards**,
    otherwise.
    
    +------------------------+--------------------------------------------------------------------------------------------------------+
    | Name (Value)           | Description                                                                                            |
    +========================+========================================================================================================+
    | Release 8-10 (0)       | Specifies the mask type to be used for UE, supporting 3GPP Release 8 to 3GPP Release 10 specification. |
    +------------------------+--------------------------------------------------------------------------------------------------------+
    | Release 11 Onwards (1) | Specifies the mask type to be used for UE, supporting 3GPP Release 11 and higher specification.        |
    +------------------------+--------------------------------------------------------------------------------------------------------+
    """

    MODACC_AVERAGING_ENABLED = 3162122
    r"""Specifies whether to enable averaging for the ModAcc measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the ModAcc Averaging   |
    |              | Count attribute.                                                                                                         |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_AVERAGING_COUNT = 3162123
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    MODACC_ALL_TRACES_ENABLED = 3162125
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    MODACC_NUMBER_OF_ANALYSIS_THREADS = 3162126
    r"""Specifies the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
    range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
    number of threads used depends on the problem size, system resources, data availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    MODACC_PRE_FFT_ERROR_ESTIMATION_INTERVAL = 3162239
    r"""Specifies the interval used for Pre-FFT Error Estimation.
    
    Pre-FFT Error Estimation Interval set to **Slot** is valid only when the
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Uplink**.
    Pre-FFT Error Estimation Interval set to **Subframe** is valid only when the
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Downlink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Measurement Length**.
    
    +------------------------+----------------------------------------------------------------------------------------------+
    | Name (Value)           | Description                                                                                  |
    +========================+==============================================================================================+
    | Slot (0)               | Frequency and Timing Error is estimated per slot in the pre-fft domain.                      |
    +------------------------+----------------------------------------------------------------------------------------------+
    | Subframe (1)           | Frequency and Timing Error is estimated per subframe in the pre-fft domain.                  |
    +------------------------+----------------------------------------------------------------------------------------------+
    | Measurement Length (2) | Frequency and Timing Error is estimated over the measurement interval in the pre-fft domain. |
    +------------------------+----------------------------------------------------------------------------------------------+
    """

    MODACC_SYMBOL_CLOCK_ERROR_ESTIMATION_ENABLED = 3162240
    r"""Specifies whether to estimate symbol clock error.
    
    If symbol clock error is not present in the signal to be analyzed, symbol clock error estimation may be
    disabled to reduce measurement time or to avoid measurement inaccuracy due to error in symbol clock error estimation.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+-----------------------------------------------------------+
    | Name (Value) | Description                                               |
    +==============+===========================================================+
    | False (0)    | Symbol Clock Error estimation and correction is disabled. |
    +--------------+-----------------------------------------------------------+
    | True (1)     | Symbol Clock Error estimation and correction is enabled.  |
    +--------------+-----------------------------------------------------------+
    """

    MODACC_TIMING_TRACKING_ENABLED = 3162241
    r"""Specifies whether timing tracking is enabled.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+------------------------------------------------------------------+
    | Name (Value) | Description                                                      |
    +==============+==================================================================+
    | False (0)    | Disables the Timing Tracking.                                    |
    +--------------+------------------------------------------------------------------+
    | True (1)     | All the reference and data symbols are used for Timing Tracking. |
    +--------------+------------------------------------------------------------------+
    """

    MODACC_PHASE_TRACKING_ENABLED = 3162242
    r"""Specifies whether phase tracking is enabled.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+-----------------------------------------------------------------+
    | Name (Value) | Description                                                     |
    +==============+=================================================================+
    | False (0)    | Disables the Phase Tracking.                                    |
    +--------------+-----------------------------------------------------------------+
    | True (1)     | All the reference and data symbols are used for Phase Tracking. |
    +--------------+-----------------------------------------------------------------+
    """

    MODACC_RESULTS_MEAN_RMS_COMPOSITE_EVM = 3162127
    r"""Returns the mean value of the RMS EVMs calculated on all the configured channels, over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM = 3162128
    r"""Returns the maximum value of the peak EVMs calculated on all the configured channels over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_COMPOSITE_MAGNITUDE_ERROR = 3162170
    r"""Returns the RMS mean value of the composite magnitude error calculated over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_MAGNITUDE_ERROR = 3162171
    r"""Returns the peak value of the composite magnitude error calculated over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_COMPOSITE_PHASE_ERROR = 3162172
    r"""Returns the RMS mean value of the composite phase error calculated over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all the configured channels. This
    value is expressed in degrees.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_PHASE_ERROR = 3162173
    r"""Returns the peak value of phase error calculated over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute on all thee configured channels. This
    value is expressed in degrees.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PEAK_COMPOSITE_EVM_SLOT_INDEX = 3162131
    r"""Returns the slot index where the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM`
    occurs.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PEAK_COMPOSITE_EVM_SYMBOL_INDEX = 3162132
    r"""Returns the symbol index of the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM`
    attribute.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PEAK_COMPOSITE_EVM_SUBCARRIER_INDEX = 3162133
    r"""Returns the subcarrier index where the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_RESULTS_MAXIMUM_PEAK_COMPOSITE_EVM` for ModAcc occurs.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PDSCH_MEAN_RMS_EVM = 3162180
    r"""Returns the mean value of RMS EVMs calculated on PDSCH data symbols over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PDSCH_MEAN_RMS_QPSK_EVM = 3162181
    r"""Returns the mean value of RMS EVMs calculated on all QPSK modulated PDSCH resource blocks over the slots specified by
    the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PDSCH_MEAN_RMS_16QAM_EVM = 3162182
    r"""Returns the mean value of RMS EVMs calculated on all 16QAM modulated PDSCH resource blocks over the slots specified by
    the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PDSCH_MEAN_RMS_64QAM_EVM = 3162183
    r"""Returns the mean value of RMS EVMs calculated on all 64 QAM modulated PDSCH resource blocks over the slots specified by
    the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PDSCH_MEAN_RMS_256QAM_EVM = 3162184
    r"""Returns the mean value of RMS EVMs calculated on all 256 QAM modulated PDSCH resource blocks over the slots specified
    by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PDSCH_MEAN_RMS_1024QAM_EVM = 3162205
    r"""Returns the mean value of RMS EVMs calculated on all 1024 QAM modulated PDSCH resource blocks over the slots specified
    by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_CSRS_EVM = 3162185
    r"""Returns the mean value of RMS EVMs calculated on RS resource elements over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_PSS_EVM = 3162186
    r"""Returns the mean value of RMS EVMs calculated on primary synchronization signal (PSS) channel over the slots specified
    by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_SSS_EVM = 3162187
    r"""Returns the mean value of RMS EVMs calculated on secondary synchronization signal (SSS) channel over the slots
    specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_PBCH_EVM = 3162188
    r"""Returns the mean value of RMS EVMs calculated on PBCH channel over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_PCFICH_EVM = 3162189
    r"""Returns the mean value of RMS EVMs calculated on PCFICH channel over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_PDCCH_EVM = 3162190
    r"""Returns the mean value of RMS EVMs calculated on PDCCH channel over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_PHICH_EVM = 3162191
    r"""Returns the mean value of RMS EVMs calculated on PHICH channel over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_DOWNLINK_RS_TRANSMIT_POWER = 3162193
    r"""Returns the mean value of power calculated on cell-specific reference signal (CSRS) resource elements over the slots
    specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
    expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_DOWNLINK_OFDM_SYMBOL_TRANSMIT_POWER = 3162194
    r"""Returns the mean value of power calculated in one OFDM symbol over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_DOWNLINK_DETECTED_CELL_ID = 3162195
    r"""Returns the detected cell ID value.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_NPSS_EVM = 3162254
    r"""Returns the mean value of RMS EVMs calculated on NB-IoT primary synchronization signal (NPSS) channel over the slots
    specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_NSSS_EVM = 3162255
    r"""Returns the mean value of RMS EVMs calculated on NB-IoT secondary synchronization signal (NSSS) channel over the slots
    specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_NPDSCH_MEAN_RMS_EVM = 3162256
    r"""Returns the mean value of RMS EVMs calculated on the NB-IoT downlink shared channel (NPDSCH) data symbols over the
    slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_NPDSCH_MEAN_RMS_QPSK_EVM = 3162257
    r"""Returns the mean value of RMS EVMs calculated on all QPSK modulated NPDSCH subframes/slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_NRS_EVM = 3162259
    r"""Returns the mean value of RMS EVMs calculated on NRS resource elements over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_DOWNLINK_NRS_TRANSMIT_POWER = 3162260
    r"""Returns the mean value of power calculated on NB-IoT downlink reference signal (NRS) resource elements over the slots
    specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
    expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_IN_BAND_EMISSION_MARGIN = 3162155
    r"""Returns the in-band emission margin. This value is expressed in dB.
    
    The margin is the lowest difference between the in-band emission measurement trace and the limit trace. The
    limit is defined in section 6.5.2.3.5 of the *3GPP TS 36.521* specification.
    
    The in-band emissions are a measure of the interference falling into the non-allocated resources blocks.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_TO_RANGE1_MINIMUM = 3162156
    r"""Returns the peak-to-peak ripple of the EVM equalizer coefficients within the frequency *Range1*. This value is
    expressed in dB.
    
    The frequency *Range1* is defined in section 6.5.2.4.5 of the *3GPP TS 36.521* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_TO_RANGE2_MINIMUM = 3162157
    r"""Returns the peak-to-peak ripple of the EVM equalizer coefficients within the frequency *Measurement Offset* parameter.
    This value is expressed in dB.
    
    The frequency *Measurement Offset* parameter is defined in section 6.5.2.4.5 of the *3GPP TS 36.521*
    specification.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_TO_RANGE2_MINIMUM = 3162158
    r"""Returns the peak-to-peak ripple of the EVM equalizer coefficients from the frequency *Range1* to the frequency
    *Measurement Offset* parameter. The frequency *Range1* and frequency *Measurement Offset* parameter are defined in the
    section 6.5.2.4.5 of the *3GPP TS 36.521* specification. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PUSCH_MEAN_RMS_DATA_EVM = 3162134
    r"""Returns the mean value of the RMS EVMs calculated on the physical uplink shared channel (PUSCH) data symbols over the
    slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PUSCH_MAXIMUM_PEAK_DATA_EVM = 3162135
    r"""Returns the maximum value of the peak EVMs calculated on the physical uplink shared channel (PUSCH) data symbols over
    the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PUSCH_MEAN_RMS_DMRS_EVM = 3162136
    r"""Returns the mean value of the RMS EVMs calculated on the PUSCH DMRS over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PUSCH_MAXIMUM_PEAK_DMRS_EVM = 3162137
    r"""Returns the maximum value of the peak EVMs calculated on PUSCH DMRS over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PUSCH_MEAN_DATA_POWER = 3162138
    r"""Returns the mean value of the power calculated on the physical uplink shared channel (PUSCH) data symbols over the
    slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
    expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PUSCH_MEAN_DMRS_POWER = 3162139
    r"""Returns the mean value of the power calculated on the PUSCH DMRS over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_RMS_SRS_EVM = 3162178
    r"""Returns the mean value of RMS EVMs calculated on the SRS symbols over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_SRS_POWER = 3162179
    r"""Returns the mean value of power calculated on SRS over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This values is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_NPUSCH_MEAN_RMS_DATA_EVM = 3162218
    r"""Returns the mean value of RMS EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) data symbols
    over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **percentage**, the
    result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
    dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_NPUSCH_MAXIMUM_PEAK_DATA_EVM = 3162219
    r"""Returns the maximum value of peak EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) data
    symbols over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
    attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **percentage**, the
    result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
    dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    The default value is 0.
    """

    MODACC_RESULTS_NPUSCH_MEAN_RMS_DMRS_EVM = 3162220
    r"""Returns the mean value of RMS EVMs calculated on the narrowband physical uplink shared channel (NPUSCH) DMRS over the
    slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
    dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    The default value is 0.
    """

    MODACC_RESULTS_NPUSCH_MAXIMUM_PEAK_DMRS_EVM = 3162221
    r"""Returns the maximum value of peak EVMs calculated on NPUSCH DMRS over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    result is returned as a percentage, and when you set the ModAcc EVM Unit attribute to **dB**, the result is returned in
    dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    The default value is 0.
    """

    MODACC_RESULTS_NPUSCH_MEAN_DATA_POWER = 3162222
    r"""Returns the mean value of the power calculated on the narrowband physical uplink shared channel (NPUSCH) data symbols
    over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This
    value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    The default value is 0.
    """

    MODACC_RESULTS_NPUSCH_MEAN_DMRS_POWER = 3162223
    r"""Returns the mean value of the power calculated on the narrowband physical uplink shared channel (NPUSCH) DMRS over the
    slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_TO_RANGE1_MINIMUM = 3162159
    r"""Returns the peak-to-peak ripple of the EVM equalizer coefficients from frequency *Measurement Offset* parameter to
    frequency *Range1*. This value is expressed in dB.
    
    The frequency *Range1* and frequency *Measurement Offset* parameter are defined in section 6.5.2.4.5 of the
    *3GPP TS 36.521* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_SUBBLOCK_IN_BAND_EMISSION_MARGIN = 3162174
    r"""Returns the in-band emission margin of a subblock aggregated bandwidth. This value is expressed in dB.
    
    The margin is the lowest difference between the in-band emission measurement trace and the limit trace. The
    limit is defined in section 6.5.2A.3 of the *3GPP TS 36.521* specification.
    
    The in-band emissions are a measure of the interference falling into the non-allocated resources blocks. The
    result of this attribute is valid only when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per Subblock**.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PSSCH_MEAN_RMS_DATA_EVM = 3162227
    r"""Returns the mean value of the RMS EVMs calculated on the physical sidelink shared channel (PSSCH) data symbols over the
    slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PSSCH_MAXIMUM_PEAK_DATA_EVM = 3162228
    r"""Returns the maximum value of the peak EVMs calculated on the physical sidelink shared channel (PSSCH) data symbols over
    the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PSSCH_MEAN_RMS_DMRS_EVM = 3162229
    r"""Returns the mean value of the RMS EVMs calculated on the PSSCH DMRS symbols over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PSSCH_MAXIMUM_PEAK_DMRS_EVM = 3162230
    r"""Returns the maximum value of the peak EVMs calculated on PSSCH DMRS symbols over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PSSCH_MEAN_DATA_POWER = 3162231
    r"""Returns the mean value of the power calculated on the physical sidelink shared channel (PSSCH) data symbols over the
    slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is
    expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_PSSCH_MEAN_DMRS_POWER = 3162232
    r"""Returns the mean value of the power calculated on the PSSCH DMRS symbols over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_FREQUENCY_ERROR = 3162146
    r"""Returns the estimated carrier frequency offset averaged over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MAXIMUM_PEAK_FREQUENCY_ERROR = 3162243
    r"""Returns the estimated maximum carrier frequency offset per slot in case of **Uplink** and per subframe in case of
    **Downlink** over the slots specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
    attribute. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_IQ_ORIGIN_OFFSET = 3162147
    r"""Returns the estimated I/Q origin offset averaged over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBc.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**. This result will not be measured in case of downlink.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MAXIMUM_PEAK_IQ_ORIGIN_OFFSET = 3162160
    r"""Returns the estimated maximum IQ origin offset over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dBc.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink**. This result will not be measured in case of **Downlink**.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_IQ_GAIN_IMBALANCE = 3162148
    r"""Returns the estimated I/Q gain imbalance averaged over the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`. The I/Q gain imbalance is the ratio of the
    amplitude of the I component to the Q component of the I/Q signal being measured. This value is expressed in dB.
    
    .. note::
       When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` attribute to **200.0 k** and
       the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 12, this result is available. For
       other values of NPUSCH Num Tones, this result will be reported as NaN.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_QUADRATURE_ERROR = 3162149
    r"""Returns the estimated quadrature error averaged over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute.  This value is expressed in degrees.
    
    Quadrature error is a measure of the skewness of the I component with respect to the Q component of the I/Q
    signal being measured.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` attribute to **200.0
    k** and the :py:attr:`~nirfmxlte.attributes.AttributeID.NPUSCH_NUMBER_OF_TONES` attribute to 12, this result is
    available. For other values of NPUSCH Num Tones, this result will be reported as NaN.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_IQ_TIMING_SKEW = 3162150
    r"""Returns the estimated IQ timing skew averaged over measured length. IQ timing skew is the difference between the group
    delay of the in-phase (I) and quadrature (Q) components of the signal. This value is expressed in seconds.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_TIME_OFFSET = 3162151
    r"""Returns the time difference between the detected slot or frame boundary and the reference trigger location depending on
    the value of :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. This value is
    expressed in seconds.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_MEAN_SYMBOL_CLOCK_ERROR = 3162152
    r"""Returns the estimated symbol clock error averaged over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in ppm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    MODACC_RESULTS_SUBBLOCK_MEAN_IQ_ORIGIN_OFFSET = 3162175
    r"""Returns the estimated I/Q origin offset averaged over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute in the subblock. This value is
    expressed in dBc.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
    per Subblock**.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    MODACC_RESULTS_SUBBLOCK_MEAN_IQ_GAIN_IMBALANCE = 3162176
    r"""Returns the estimated I/Q gain imbalance averaged over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in dB. The
    I/Q gain imbalance is the ratio of the amplitude of the I component to the Q component of the I/Q signal being measured
    in the subblock.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
    per Subblock**. Otherwise, this parameter returns NaN, as measurement of this result is currently not supported.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    MODACC_RESULTS_SUBBLOCK_MEAN_QUADRATURE_ERROR = 3162177
    r"""Returns the estimated quadrature error averaged over the slots specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. This value is expressed in degrees.
    Quadrature error is a measure of the skewness of the I component with respect to the Q component of the I/Q signal
    being measured in the subblock.
    
    This result is valid only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Uplink** and the :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO
    per Subblock**. Otherwise, this parameter returns NaN, as measurement of this result is currently not supported.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    ACP_MEASUREMENT_ENABLED = 3149824
    r"""Specifies whether to enable the ACP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    ACP_SUBBLOCK_INTEGRATION_BANDWIDTH = 3149887
    r"""Specifies the integration bandwidth of the subblock. This value is expressed in Hz. Integration bandwidth is the span
    from the left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock.
    
    Use "subblock<*n*>" as the selector string to read this result.
    
    The default value is 0.
    """

    ACP_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH = 3149829
    r"""Specifies the integration bandwidth of the component carrier (CC). This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    The default value is 9 MHz.
    """

    ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED = 3149892
    r"""Specifies whether the number of offsets is computed by measurement or configured by you.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    When the carrier bandwidth is 200 kHz or the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` is
    **Downlink**, the default value is **False**. The default value is **True**, otherwise.
    
    .. note::
       In case of downlink, this attribute is valid only for number of E-UTRA offsets. For the number of UTRA offsets, only
       3GPP specification defined values are supported.
    
    +--------------+-----------------------------------------------------------------------+
    | Name (Value) | Description                                                           |
    +==============+=======================================================================+
    | False (0)    | Measurement will set the number of offsets.                           |
    +--------------+-----------------------------------------------------------------------+
    | True (1)     | Measurement will use the user configured value for number of offsets. |
    +--------------+-----------------------------------------------------------------------+
    """

    ACP_NUMBER_OF_UTRA_OFFSETS = 3149882
    r"""Specifies the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
    positions, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED`
    attribute to **True**.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is 1, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` to **Uplink**.
    
    The default value is 0, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` to **Downlink**.
    
    The default value is 0, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.BAND` attribute to 46 or
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute to **LAA**.
    
    The default value is 2 for all other configurations.
    
    .. note::
       In case of downlink, only 3GPP specification defined values are supported. In case of non-contiguous carrier
       aggregation, the configured value will be used only for the outer offsets and the offset channels in the gap region are
       defined as per the 3GPP specification. Offset power reference for the outer UTRA offsets are set according to the value
       of :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute.
    """

    ACP_NUMBER_OF_EUTRA_OFFSETS = 3149883
    r"""Specifies the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
    at offset positions, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is 0, when carrier bandwidth is 200 kHz. The default value is 2 for downlink and 1 for
    uplink, otherwise.
    
    .. note::
       In case of non-contiguous carrier aggregation, the configured value will be used only for the outer offsets and the
       offset channels in the gap region are defined as per the 3GPP specification. Offset integration bandwidth and offset
       power reference for the outer E-UTRA offsets are set according to the value of
       :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_EUTRA_OFFSET_DEFINITION` attribute.
    """

    ACP_EUTRA_OFFSET_DEFINITION = 3149891
    r"""Specifies the evolved universal terrestrial radio access (E-UTRA) offset channel definition.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    .. note::
       In case of non-contiguous, the inner offset channel definition will be configured internally as per the 3GPP
       specification. Offset power reference for the outer UTRA offsets are set according to ACP EUTRA Offset Definition
       attribute.
    
    The default value is **Auto**.
    
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)  | Description                                                                                                              |
    +===============+==========================================================================================================================+
    | Auto (0)      | Measurement will set the E-UTRA definition and offset power reference based on the link direction. For downlink, the     |
    |               | definition is Closest and for uplink, it is Composite.                                                                   |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Closest (1)   | Integration bandwidth is derived from the closest LTE carrier. Offset power reference is set to Closest internally.      |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Composite (2) | Integration bandwidth is derived from the aggregated sub-block bandwidth. Offset power reference is set as Composite     |
    |               | Sub-Block.                                                                                                               |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_NUMBER_OF_GSM_OFFSETS = 3149890
    r"""Specifies the number of GSM adjacent channel offsets to be configured when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` to **200.0 k** and the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_CONFIGURABLE_NUMBER_OF_OFFSETS_ENABLED` attribute to **True**.
    
    The frequency offset from the center of NB-IOT carrier to the center of the first offset is 300 kHz as defined
    in the 3GPP specification. The center of every other offset is placed at 200 kHz from the previous offset's center.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is 1, when you set the CC Bandwidth attribute to is **200.0 k**. The default value is 0,
    otherwise.
    """

    ACP_OFFSET_FREQUENCY = 3149834
    r"""Specifies the offset frequency of an offset channel. This value is expressed in Hz. When you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Uplink**, the offset frequency is computed
    from the center of a reference component carrier/subblock to the center of the nearest RBW filter of the offset
    channel.
    When you set the Link Direction attribute to **Downlink**, the offset frequency is computed from the center of
    the closest component carrier to the center of the nearest RBW filter of the offset channel.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    
    The default value is 10 MHz.
    """

    ACP_OFFSET_INTEGRATION_BANDWIDTH = 3149838
    r"""Specifies the integration bandwidth of an offset carrier. This value is expressed in Hz.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    
    The default value is 9 MHz.
    """

    ACP_RBW_FILTER_AUTO_BANDWIDTH = 3149851
    r"""Specifies whether the measurement computes the RBW.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+-------------------------------------------------------------------------+
    | Name (Value) | Description                                                             |
    +==============+=========================================================================+
    | False (0)    | The measurement uses the RBW that you specify in the ACP RBW attribute. |
    +--------------+-------------------------------------------------------------------------+
    | True (1)     | The measurement computes the RBW.                                       |
    +--------------+-------------------------------------------------------------------------+
    """

    ACP_RBW_FILTER_BANDWIDTH = 3149852
    r"""Specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
    expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 30000.
    """

    ACP_RBW_FILTER_TYPE = 3149853
    r"""Specifies the shape of the RBW filter.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **FFT Based**.
    
    +---------------+----------------------------------------------------+
    | Name (Value)  | Description                                        |
    +===============+====================================================+
    | FFT Based (0) | No RBW filtering is performed.                     |
    +---------------+----------------------------------------------------+
    | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
    +---------------+----------------------------------------------------+
    | Flat (2)      | An RBW filter with a flat response is applied.     |
    +---------------+----------------------------------------------------+
    """

    ACP_SWEEP_TIME_AUTO = 3149854
    r"""Specifies whether the measurement computes the sweep time.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+---------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                           |
    +==============+=======================================================================================+
    | False (0)    | The measurement uses the sweep time that you specify in the ACP Sweep Time attribute. |
    +--------------+---------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
    +--------------+---------------------------------------------------------------------------------------+
    """

    ACP_SWEEP_TIME_INTERVAL = 3149855
    r"""Specifies the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
    **False**. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    ACP_POWER_UNITS = 3149843
    r"""Specifies the units for absolute power.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **dBm**.
    
    +--------------+---------------------------------------------+
    | Name (Value) | Description                                 |
    +==============+=============================================+
    | dBm (0)      | The absolute powers are reported in dBm.    |
    +--------------+---------------------------------------------+
    | dBm/Hz (1)   | The absolute powers are reported in dBm/Hz. |
    +--------------+---------------------------------------------+
    """

    ACP_MEASUREMENT_METHOD = 3149842
    r"""Specifies the method for performing the ACP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Normal**.
    
    +--------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)       | Description                                                                                                              |
    +====================+==========================================================================================================================+
    | Normal (0)         | The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this        |
    |                    | method when measurement speed is desirable over higher dynamic range.                                                    |
    +--------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Dynamic Range (1)  | The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use   |
    |                    | this method to get the best dynamic range. Supported Devices: PXIe-5665/5668                                             |
    +--------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Sequential FFT (2) | The ACP measurement acquires all the samples specified by the ACP Sweep Time attribute and divides them in to smaller    |
    |                    | chunks of equal size defined by the ACP Sequential FFT Size attribute.                                                   |
    |                    | FFT is computed for each chunk. The resultant FFTs are averaged to get the spectrum used to compute the ACP.             |
    |                    | If the total acquired samples is not an integer multiple of the FFT size, the remaining samples at the end of the        |
    |                    | acquisition are not used.                                                                                                |
    +--------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_NOISE_CALIBRATION_MODE = 3149899
    r"""Specifies whether the noise calibration and measurement is performed automatically by the measurement or by you.  Refer
    to the measurement guidelines section in the `Noise Compensation Algorithm
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Auto**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Manual (0)   | When you set the ACP Meas Mode attribute to Calibrate Noise Floor, you can initiate instrument noise calibration for     |
    |              | ACP measurement manually. When you set the ACP Meas Mode attribute to Measure, you can initiate the ACP measurement      |
    |              | manually.                                                                                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Auto (1)     | When you set the ACP Noise Comp Enabled attribute to True, RFmx sets the Input Isolation Enabled attribute to Enabled    |
    |              | and calibrates the instrument noise in the current state of the instrument. RFmx then resets Input Isolation Enabled     |
    |              | attribute and performs the ACP measurement including compensation for the noise contribution of the instrument. RFmx     |
    |              | skips noise calibration in this mode if valid noise calibration data is already cached.                                  |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_NOISE_CALIBRATION_AVERAGING_AUTO = 3149898
    r"""Specifies whether RFmx automatically computes the averaging count used for instrument noise calibration.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+----------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                      |
    +==============+==================================================================================+
    | False (0)    | RFmx uses the averages that you set for ACP Noise Cal Averaging Count attribute. |
    +--------------+----------------------------------------------------------------------------------+
    | True (1)     | RFmx uses the following averaging counts:                                        |
    +--------------+----------------------------------------------------------------------------------+
    """

    ACP_NOISE_CALIBRATION_AVERAGING_COUNT = 3149897
    r"""Specifies the averaging count used for noise calibration when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 32.
    """

    ACP_NOISE_COMPENSATION_ENABLED = 3149856
    r"""Specifies whether RFmx compensates for the instrument noise while performing the measurement when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set the ACP
    Noise Cal Mode attribute to **Manual** and the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_MODE`
    attribute to **Measure**. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | Disables compensation of the channel powers for the noise floor of the signal analyzer.                                  |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | Enables compensation of the channel powers for the noise floor of the signal analyzer. The noise floor of the signal     |
    |              | analyzer is measured for the RF path used by the ACP measurement and cached for future use. If the signal analyzer or    |
    |              | the measurement parameters change, noise floors are remeasured.                                                          |
    |              | Supported Devices: PXIe-5663/5665/5668, PXIe-5830/5831/5832/5842/5860                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_NOISE_COMPENSATION_TYPE = 3149896
    r"""Specifies the noise compensation type. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Analyzer and Termination**.
    
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)                 | Description                                                                                                              |
    +==============================+==========================================================================================================================+
    | Analyzer and Termination (0) | Compensates for noise from the analyzer and the 50 ohm termination. The measured power values are in excess of the       |
    |                              | thermal noise floor.                                                                                                     |
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Analyzer Only (1)            | Compensates for analyzer noise only.                                                                                     |
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_AVERAGING_ENABLED = 3149846
    r"""Specifies whether to enable averaging for the ACP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The ACP measurement uses the value of the ACP Averaging Count attribute as the number of acquisitions over which the     |
    |              | ACP measurement is averaged.                                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_AVERAGING_COUNT = 3149845
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    ACP_AVERAGING_TYPE = 3149848
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
    measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    Default value is **RMS**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                  |
    +==============+==============================================================================================================+
    | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations, but not the noise floor. |
    +--------------+--------------------------------------------------------------------------------------------------------------+
    | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                       |
    +--------------+--------------------------------------------------------------------------------------------------------------+
    | Scalar (2)   | The square root of the power spectrum is averaged.                                                           |
    +--------------+--------------------------------------------------------------------------------------------------------------+
    | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.           |
    +--------------+--------------------------------------------------------------------------------------------------------------+
    | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.         |
    +--------------+--------------------------------------------------------------------------------------------------------------+
    """

    ACP_MEASUREMENT_MODE = 3149895
    r"""Specifies whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement. Refer to the
    measurement guidelines section in the `Noise Compensation Algorithm
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Measure**.
    
    +---------------------------+---------------------------------------------------------------------------------------+
    | Name (Value)              | Description                                                                           |
    +===========================+=======================================================================================+
    | Measure (0)               | ACP measurement is performed on the acquired signal.                                  |
    +---------------------------+---------------------------------------------------------------------------------------+
    | Calibrate Noise Floor (1) | Manual noise calibration of the signal analyzer is performed for the ACP measurement. |
    +---------------------------+---------------------------------------------------------------------------------------+
    """

    ACP_FFT_OVERLAP_MODE = 3149893
    r"""Specifies the overlap mode when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
    attribute to **Sequential FFT**. In Sequential FFT method, the measurement divides all the acquired samples into
    smaller FFT chunks of equal size.  Then the FFT is computed for each chunk. The resultant FFTs are averaged to get the
    spectrum used to compute the ACP.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Disabled**.
    
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)     | Description                                                                                                              |
    +==================+==========================================================================================================================+
    | Disabled (0)     | Disables the overlap between the FFT chunks.                                                                             |
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Automatic (1)    | Measurement sets the                                                                                                     |
    |                  | number of overlapped samples between consecutive FFT chunks to 50% of the ACP Sequential FFT Size attribute value.       |
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    | User Defined (2) | Measurement uses the overlap that you specify in the ACP FFT Overlap attribute.                                          |
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_FFT_OVERLAP = 3149894
    r"""Specifies the samples to overlap between the consecutive chunks as a percentage of the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute value when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    ACP_IF_OUTPUT_POWER_OFFSET_AUTO = 3149876
    r"""Specifies whether the measurement computes an appropriate IF output power level offset for the offset channels to
    improve the dynamic range of the ACP measurement. This attribute is valid only when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement sets the IF output power level offset using the values of the ACP Near IF Output Pwr Offset and ACP Far  |
    |              | IF Output Pwr Offset attributes.                                                                                         |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement automatically computes an IF output power level offset for the offset channels to improve the dynamic    |
    |              | range of the ACP measurement.                                                                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_NEAR_IF_OUTPUT_POWER_OFFSET = 3149877
    r"""Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are near the
    carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
    the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    ACP_FAR_IF_OUTPUT_POWER_OFFSET = 3149878
    r"""Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
    carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is valid only when you set
    the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 20.
    """

    ACP_SEQUENTIAL_FFT_SIZE = 3149889
    r"""Specifies the FFT size, when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute
    to **Sequential FFT**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 512.
    """

    ACP_AMPLITUDE_CORRECTION_TYPE = 3149888
    r"""Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
    the RF center frequency, or at the individual frequency bins. Use the
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

    ACP_ALL_TRACES_ENABLED = 3149857
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the ACP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    ACP_NUMBER_OF_ANALYSIS_THREADS = 3149844
    r"""Specifies the maximum number of threads used for parallelism for the ACP measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    ACP_RESULTS_TOTAL_AGGREGATED_POWER = 3149858
    r"""Returns the sum of powers of all the frequency bins over the integration bandwidths of all subblocks. The sum includes
    the power in inter-carrier gaps within a subblock but it does not include the power in subblock gaps.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, the
    attribute returns the total integrated power in dBm of all the active carriers measured. When you set the ACP Pwr Units
    attribute to **dBm/Hz**, the attribute returns the power spectral density in dBm/Hz based on the power in all the
    active carriers measured.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    """

    ACP_RESULTS_SUBBLOCK_CENTER_FREQUENCY = 3149881
    r"""Returns the absolute center frequency of the subblock, which is the center of the subblock integration bandwidth.  This
    value is expressed in Hz. Integration bandwidth is the span from the left edge of the leftmost carrier to the right
    edge of the rightmost carrier within the subblock.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    ACP_RESULTS_SUBBLOCK_INTEGRATION_BANDWIDTH = 3149879
    r"""Returns the integration bandwidth used in calculating the power of the subblock. This value is expressed in Hz.
    Integration bandwidth is the span from left edge of the leftmost carrier to the right edge of the rightmost carrier
    within the subblock.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    ACP_RESULTS_SUBBLOCK_POWER = 3149880
    r"""Returns the sum of powers of all the frequency bins over the integration bandwidth of the subblock.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, the
    attribute returns the total subblock power in dBm of all the active carriers measured over the subblock. When you set
    the ACP Pwr Units attribute to **dBm/Hz**, the attribute returns the power spectral density in dBm/Hz based on the
    power in all the active carriers measured over the subblock.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    ACP_RESULTS_COMPONENT_CARRIER_ABSOLUTE_POWER = 3149862
    r"""Returns the power measured over the integration bandwidth of the carrier. The carrier power is reported in dBm when you
    set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set
    the ACP Pwr Units attribute to **dBm/Hz**.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    ACP_RESULTS_COMPONENT_CARRIER_RELATIVE_POWER = 3149863
    r"""Returns the component carrier power relative to its subblock power. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    ACP_RESULTS_LOWER_OFFSET_ABSOLUTE_POWER = 3149868
    r"""Returns the lower (negative) offset channel power. If this offset is not applicable for the intra-band non-contiguous
    type of carrier aggregation, a NaN is returned. The offset channel power is reported in dBm when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
    Pwr Units attribute to **dBm/Hz**.
    
    Refer to the *3GPP 36.521* specification for more information about the applicability of an offset channel.
    Refer to the `LTE Uplink Adjacent Channel Power
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-adjacent-channel-power.html>`_ and `LTE Downlink
    Adjacent Channel Power <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-adjacent-channel-power.html>`_ topics
    for more information.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    ACP_RESULTS_LOWER_OFFSET_RELATIVE_POWER = 3149869
    r"""Returns the power in lower (negative) offset channel relative to the total  aggregated power. This value is expressed
    in dB. If this offset is not applicable for the intra-band non-contiguous type of carrier aggregation, a NaN is
    returned.
    
    Refer to the *3GPP TS 36.521* specification for more information about the applicability of the offset channel.
    Refer to the `LTE Uplink Adjacent Channel Power
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-adjacent-channel-power.html>`_ and `LTE Downlink
    Adjacent Channel Power <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-adjacent-channel-power.html>`_ topics
    for more information.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    ACP_RESULTS_UPPER_OFFSET_ABSOLUTE_POWER = 3149874
    r"""Returns the upper (positive) offset channel power. If this offset is not applicable for the intra-band non-contiguous
    type of carrier aggregation, a NaN is returned. The offset channel power is reported in dBm when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
    Pwr Units attribute to **dBm/Hz**.
    
    Refer to the *3GPP TS 36.521* specification for more information about the applicability of offset channel.
    Refer to the `LTE Uplink Adjacent Channel Power
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-adjacent-channel-power.html>`_ and `LTE Downlink
    Adjacent Channel Power <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-adjacent-channel-power.html>`_ topics
    for more information about ACP offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    ACP_RESULTS_UPPER_OFFSET_RELATIVE_POWER = 3149875
    r"""Returns the power in the upper (positive) offset channel relative to the total aggregated power. This value is
    expressed in dB. If this offset is not applicable for the intra band non contagious type of carrier aggregation, a Nan
    is returned.. Refer to the *3GPP TS 36.521* specification for more information about the applicability of the offset
    channel.
    
    Refer to the `LTE Uplink Adjacent Channel Power
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-adjacent-channel-power.html>`_ and `LTE Downlink
    Adjacent Channel Power <www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-adjacent-channel-power.html>`_ topics
    for more information about ACP offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    CHP_MEASUREMENT_ENABLED = 3158016
    r"""Specifies whether to enable the channel power measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    CHP_INTEGRATION_BANDWIDTH_TYPE = 3158040
    r"""Specifies the integration bandwidth (IBW) type used to measure the power of the acquired signal. Integration bandwidth
    is the frequency interval over which the power in each frequency bin is added to measure the total power in that
    interval.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    Refer to the `LTE Channel Power <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-channel-power.html>`_
    topic for more information about CHP IBW types.
    
    The default value is **Signal Bandwidth**.
    
    +-----------------------+---------------------------------------------------------------------------+
    | Name (Value)          | Description                                                               |
    +=======================+===========================================================================+
    | Signal Bandwidth (0)  | The IBW excludes the guard bands at the edges of the carrier or subblock. |
    +-----------------------+---------------------------------------------------------------------------+
    | Channel Bandwidth (1) | The IBW includes the guard bands at the edges of the carrier or subblock. |
    +-----------------------+---------------------------------------------------------------------------+
    """

    CHP_SUBBLOCK_INTEGRATION_BANDWIDTH = 3158050
    r"""Specifies the integration bandwidth of a subblock. This value is expressed in Hz. Integration bandwidth is the span
    from the left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock.
    
    Use "subblock<*n*>" as the selector string to read this result.
    
    The default value is 0.
    """

    CHP_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH = 3158018
    r"""Specifies the integration bandwidth of a component carrier. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    The default value is 9 MHz.
    """

    CHP_RBW_FILTER_AUTO_BANDWIDTH = 3158028
    r"""Specifies whether the CHP measurement computes the RBW.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                  |
    +==============+==============================================================================+
    | False (0)    | The measurement uses the RBW that you specify in the CHP RBW (Hz) attribute. |
    +--------------+------------------------------------------------------------------------------+
    | True (1)     | The measurement computes the RBW.                                            |
    +--------------+------------------------------------------------------------------------------+
    """

    CHP_RBW_FILTER_BANDWIDTH = 3158029
    r"""Specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_RBW_FILTER_AUTO_BANDWIDTH` attribute to  **False**. This value is
    expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 30000.
    """

    CHP_RBW_FILTER_TYPE = 3158030
    r"""Specifies the shape of the digital RBW filter.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **FFT Based**.
    
    +---------------+----------------------------------------------------+
    | Name (Value)  | Description                                        |
    +===============+====================================================+
    | FFT Based (0) | No RBW filtering is performed.                     |
    +---------------+----------------------------------------------------+
    | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
    +---------------+----------------------------------------------------+
    | Flat (2)      | An RBW filter with a flat response is applied.     |
    +---------------+----------------------------------------------------+
    """

    CHP_SWEEP_TIME_AUTO = 3158033
    r"""Specifies whether the measurement computes the sweep time.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+---------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                           |
    +==============+=======================================================================================+
    | False (0)    | The measurement uses the sweep time that you specify in the CHP Sweep Time attribute. |
    +--------------+---------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
    +--------------+---------------------------------------------------------------------------------------+
    """

    CHP_SWEEP_TIME_INTERVAL = 3158034
    r"""Specifies the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_SWEEP_TIME_AUTO` attribute to
    **False**. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    CHP_NOISE_CALIBRATION_MODE = 3158057
    r"""Specifies whether the noise calibration and measurement is performed automatically by the measurement or initiated by
    you.  Refer to the measurement guidelines section in the `Noise Compensation Algorithm
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Auto**
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Manual (0)   | When you set the CHP Meas Mode attribute to Calibrate Noise Floor, you can initiate instrument noise calibration for     |
    |              | CHP measurement manually. When you set the CHP Meas Mode attribute to Measure, you can initiate the CHP measurement      |
    |              | manually.                                                                                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Auto (1)     | When you set the CHP Noise Comp Enabled attribute to True, RFmx sets the Input Isolation Enabled attribute to Enabled    |
    |              | and calibrates the instrument noise in the current state of the instrument. RFmx then resets the Input Isolation         |
    |              | Enabled attribute and performs the CHP measurement, including compensation for the noise contribution of the             |
    |              | instrument. RFmx skips noise calibration in this mode if valid noise calibration data is already cached.                 |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    CHP_NOISE_CALIBRATION_AVERAGING_AUTO = 3158056
    r"""Specifies whether RFmx automatically computes the averaging count used for instrument noise calibration.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                          |
    +==============+======================================================================================+
    | False (0)    | RFmx uses the averages that you set for the CHP Noise Cal Averaging Count attribute. |
    +--------------+--------------------------------------------------------------------------------------+
    | True (1)     | RFmx uses a noise calibration averaging count of 32.                                 |
    +--------------+--------------------------------------------------------------------------------------+
    """

    CHP_NOISE_CALIBRATION_AVERAGING_COUNT = 3158055
    r"""Specifies the averaging count used for noise calibration when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 32.
    """

    CHP_NOISE_COMPENSATION_ENABLED = 3158053
    r"""Specifies whether RFmx compensates for the instrument noise when performing the measurement. To compensate for
    instrument noise when performing a CHP measurement, set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or set the CHP Noise Cal
    Mode attribute to **Manual** and the :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_MEASUREMENT_MODE` attribute to
    **Measure**. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+------------------------------+
    | Name (Value) | Description                  |
    +==============+==============================+
    | False (0)    | Disables noise compensation. |
    +--------------+------------------------------+
    | True (1)     | Enables noise compensation.  |
    +--------------+------------------------------+
    """

    CHP_NOISE_COMPENSATION_TYPE = 3158054
    r"""Specifies the noise compensation type. Refer to the measurement guidelines section in the `Noise Compensation Algorithm
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Analyzer and Termination**.
    
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)                 | Description                                                                                                              |
    +==============================+==========================================================================================================================+
    | Analyzer and Termination (0) | Compensates for noise from the analyzer and the 50 ohm termination. The measured power values are in excess of the       |
    |                              | thermal noise floor.                                                                                                     |
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Analyzer Only (1)            | Compensates only for analyzer noise.                                                                                     |
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    CHP_AVERAGING_ENABLED = 3158023
    r"""Specifies whether to enable averaging for the CHP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The CHP measurement uses the value of the CHP Averaging Count attribute as the number of acquisitions over which the     |
    |              | CHP measurement is averaged.                                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    CHP_AVERAGING_COUNT = 3158022
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    CHP_AVERAGING_TYPE = 3158025
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for CHP
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
    | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.          |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.        |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    """

    CHP_MEASUREMENT_MODE = 3158052
    r"""Specifies whether the measurement calibrates the noise floor of analyzer or performs the CHP measurement. Refer to the
    measurement guidelines section in the `Noise Compensation Algorithm
    <www.ni.com/docs/en-US/bundle/rfmx-lte/page/noise-compensation-algorithm.html>`_ topic for more information.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Measure**.
    
    +---------------------------+---------------------------------------------------------------------------------------+
    | Name (Value)              | Description                                                                           |
    +===========================+=======================================================================================+
    | Measure (0)               | CHP measurement is performed on the acquired signal.                                  |
    +---------------------------+---------------------------------------------------------------------------------------+
    | Calibrate Noise Floor (1) | Manual noise calibration of the signal analyzer is performed for the CHP measurement. |
    +---------------------------+---------------------------------------------------------------------------------------+
    """

    CHP_AMPLITUDE_CORRECTION_TYPE = 3158051
    r"""Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
    the RF center frequency, or at the individual frequency bins. Use the
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

    CHP_ALL_TRACES_ENABLED = 3158036
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the CHP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    CHP_NUMBER_OF_ANALYSIS_THREADS = 3158019
    r"""Specifies the maximum number of threads used for parallelism for the CHP measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    CHP_RESULTS_TOTAL_AGGREGATED_POWER = 3158041
    r"""Returns the total power of all the subblocks. This value is expressed in dBm. The power in each subblock is the sum of
    powers of all the frequency bins over the integration bandwidth of the subblocks. This value includes the power in the
    inter-carrier gaps within a subblock, but it does not include the power within the subblock gaps.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    """

    CHP_RESULTS_SUBBLOCK_FREQUENCY = 3158043
    r"""Returns the absolute center frequency of the subblock. This value is the center of the subblock integration bandwidth.
    Integration bandwidth is the span from left edge of the leftmost carrier to the right edge of the rightmost carrier
    within the subblock. This value is expressed in Hz.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    CHP_RESULTS_SUBBLOCK_INTEGRATION_BANDWIDTH = 3158044
    r"""Returns the integration bandwidth used in calculating the power of the subblock. Integration bandwidth is the span from
    left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock. This value is
    expressed in Hz.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    CHP_RESULTS_SUBBLOCK_POWER = 3158045
    r"""Returns the sum of total power of all the frequency bins over the integration bandwidth of the subblock. This value
    includes the power in inter-carrier gaps within a subblock. This value is expressed in dBm.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    CHP_RESULTS_COMPONENT_CARRIER_ABSOLUTE_POWER = 3158037
    r"""Returns the power measured over the integration bandwidth of the component carrier. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    CHP_RESULTS_COMPONENT_CARRIER_RELATIVE_POWER = 3158048
    r"""Returns the component carrier power relative to its subblock power. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    OBW_MEASUREMENT_ENABLED = 3170304
    r"""Specifies whether to enable the OBW measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    OBW_SPAN = 3170308
    r"""Returns the frequency search space to find the OBW. This value is expressed in Hz.
    
    Use "subblock<*n*>" as the selector string to read this result.
    
    The default value is 10 MHz.
    """

    OBW_RBW_FILTER_AUTO_BANDWIDTH = 3170316
    r"""Specifies whether the measurement computes the RBW.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+-------------------------------------------------------------------------+
    | Name (Value) | Description                                                             |
    +==============+=========================================================================+
    | False (0)    | The measurement uses the RBW that you specify in the OBW RBW attribute. |
    +--------------+-------------------------------------------------------------------------+
    | True (1)     | The measurement computes the RBW.                                       |
    +--------------+-------------------------------------------------------------------------+
    """

    OBW_RBW_FILTER_BANDWIDTH = 3170317
    r"""Specifies the bandwidth of the RBW filter used to sweep the acquired signal, when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.OBW_RBW_FILTER_AUTO_BANDWIDTH` attribute to ** False**. This value is
    expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10000.
    """

    OBW_RBW_FILTER_TYPE = 3170318
    r"""Specifies the shape of the digital RBW filter.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Gaussian**.
    
    +---------------+----------------------------------------------------+
    | Name (Value)  | Description                                        |
    +===============+====================================================+
    | FFT Based (0) | No RBW filtering is performed.                     |
    +---------------+----------------------------------------------------+
    | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
    +---------------+----------------------------------------------------+
    | Flat (2)      | An RBW filter with a flat response is applied.     |
    +---------------+----------------------------------------------------+
    """

    OBW_SWEEP_TIME_AUTO = 3170319
    r"""Specifies whether the measurement computes the sweep time.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+---------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                           |
    +==============+=======================================================================================+
    | False (0)    | The measurement uses the sweep time that you specify in the OBW Sweep Time attribute. |
    +--------------+---------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
    +--------------+---------------------------------------------------------------------------------------+
    """

    OBW_SWEEP_TIME_INTERVAL = 3170320
    r"""Specifies the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.OBW_SWEEP_TIME_AUTO` attribute to
    **False**. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    OBW_AVERAGING_ENABLED = 3170311
    r"""Specifies whether to enable averaging for the OBW measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The OBW measurement uses the value of the OBW Averaging Count attribute as the number of acquisitions over which the     |
    |              | OBW measurement is averaged.                                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    OBW_AVERAGING_COUNT = 3170310
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.OBW_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    OBW_AVERAGING_TYPE = 3170313
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for the OBW
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
    | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.          |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.        |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    """

    OBW_AMPLITUDE_CORRECTION_TYPE = 3170331
    r"""Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
    the RF center frequency, or at the individual frequency bins. Use the
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

    OBW_ALL_TRACES_ENABLED = 3170322
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the OBW measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    OBW_NUMBER_OF_ANALYSIS_THREADS = 3170307
    r"""Specifies the maximum number of threads used for parallelism for the OBW measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    OBW_RESULTS_OCCUPIED_BANDWIDTH = 3170323
    r"""Returns the bandwidth that occupies 99 percentage of the total power of the signal within a carrier/subblock. This
    value is expressed in Hz.
    
    Refer to the `LTE Occupied Bandwidth
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-occupied-bandwidth.html>`_ topic for more information.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    OBW_RESULTS_ABSOLUTE_POWER = 3170324
    r"""Returns the total power measured in the carrier/subblock. This value is expressed in dBm.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    OBW_RESULTS_START_FREQUENCY = 3170325
    r"""Returns the start frequency of the carrier/subblock. This value is expressed in Hz. The occupied bandwidth is
    calculated using the following equation:
    
    *Stop frequency* - *Start frequency* = *Occupied bandwidth*
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    OBW_RESULTS_STOP_FREQUENCY = 3170326
    r"""Returns the stop frequency of the carrier/subblock. This value is expressed in Hz. Occupied bandwidth is calculated
    using the following equation:
    
    *Occupied bandwidth* = *Stop frequency* - *Start frequency*
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    SEM_MEASUREMENT_ENABLED = 3178496
    r"""Specifies whether to enable the SEM measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal and result
    instances. Refer to the Selector String topic for information about the string syntax for named signals and named
    results.
    
    The default value is FALSE.
    """

    SEM_UPLINK_MASK_TYPE = 3178572
    r"""Specifies the spectrum emission mask used in the measurement for uplink. Each mask type refers to a different Network
    Signalled (NS) value. **General CA Class B**, **CA_NS_04**, **CA_NC_NS_01**, **CA_NS_09**, and **CA_NS_10** refers to
    the carrier aggregation case. You must set the mask type to **Custom** to configure the custom offset masks.
    Refer to section 6.6.2.1 of the *3GPP 36.521* specification for more information about standard-defined mask
    types.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **General (NS_01)**.
    
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)                         | Description                                                                                                              |
    +======================================+==========================================================================================================================+
    | General (NS_01) (0)                  | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1.5-1, 6.6.2.1.5-2,      |
    |                                      | 6.6.2.1A.5-1, 6.6.2.1A.1.5-2, 6.6.2.1A.1.5-3, and 6.6.2.1A.5-4 in section 6.6.2 of the 3GPP TS 36.521-1 specification.   |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_03 or NS_11 or NS_20 or NS_21 (1) | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.1-1 and              |
    |                                      | 6.6.2.2.5.1-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                    |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_04 (2)                            | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.3.2-3 in section       |
    |                                      | 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                             |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_06 or NS_07 (3)                   | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.3-1 and              |
    |                                      | 6.6.2.2.5.3-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                    |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | CA_NS_04 (4)                         | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.1.5.1-1 in section    |
    |                                      | 6.6.2 of the 3GPP TS 36.521-1 specification. This mask applies only for aggregated carriers.                             |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Custom (5)                           | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
    |                                      | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type,  |
    |                                      | and SEM Offset BW Integral attributes for each offset.                                                                   |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | General CA Class B (6)               | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.1A.1.5-3 and 6.6.2.1A.1.5-4  |
    |                                      | in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                  |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | CA_NC_NS_01 (7)                      | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.3.5-1 and 6.6.2.2A.3.5-2  |
    |                                      | in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                  |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_27 or NS_43 (8)                   | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5-1 in section 6.6.2.2.5   |
    |                                      | of the 3GPP TS 36.101-1 specification.                                                                                   |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_35 (9)                            | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.5-1 in section           |
    |                                      | 6.6.2.2.5.5 of the 3GPP TS 36.521-1 specification.                                                                       |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_28 (10)                           | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.6-1 in section 6.6.2.2.6   |
    |                                      | of the 3GPP TS 36.101-1 specification.                                                                                   |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | CA_NS_09 (11)                        | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.2-1 in section            |
    |                                      | 6.6.2.2A.2, and Table 6.6.2.2A.3-1 in section 6.6.2.2A.3 of the 3GPP TS 36.101-1 specification.                          |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | CA_NS_10 (12)                        | The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.4-1 in section            |
    |                                      | 6.6.2.2A.4 of the 3GPP TS 36.101-1 specification.                                                                        |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_DOWNLINK_MASK_TYPE = 3178579
    r"""Specifies the limits to be used in the measurement for downlink. Refer to section 6.6.3 of the *3GPP 36.141*
    specification for more information about standard-defined mask types.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **eNodeB Category Based**.
    
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)              | Description                                                                                                              |
    +===========================+==========================================================================================================================+
    | eNodeB Category Based (0) | The limits are applied based on eNodeB Category attribute.                                                               |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Band 46 (1)               | The limits are applied based on Band 46 test requirements.                                                               |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Custom (5)                | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
    |                           | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Rel Limit Start,                                       |
    |                           | SEM Offset Rel Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type, and SEM Offset BW Integral   |
    |                           | attributes for each offset.                                                                                              |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_SIDELINK_MASK_TYPE = 3178584
    r"""Specifies the spectrum emission mask used in the measurement for sidelink. Each mask type refers to a different Network
    Signalled (NS) value. You must set the mask type to **Custom** to configure the custom offset masks.
    Refer to section 6.6.2 of the *3GPP 36.521* specification for more information about standard-defined mask
    types.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **General (NS_01)**.
    
    +---------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)        | Description                                                                                                              |
    +=====================+==========================================================================================================================+
    | General (NS_01) (0) | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1G.1.5-1 and Table       |
    |                     | 6.6.2.1G.3.5-1 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                   |
    +---------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_33 or NS_34 (1)  | The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2G.1.5-1 in section      |
    |                     | 6.6.2 of the 3GPP TS 36.521-1 specification.                                                                             |
    +---------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Custom (5)          | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
    |                     | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type,  |
    |                     | and SEM Offset BW Integral attributes for each offset.                                                                   |
    +---------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_DELTA_F_MAXIMUM = 3178580
    r"""Specifies the stop frequency for the last offset segment to be used in the measurement. This value is expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 15 MHz. The minimum value is 9.5 MHz.
    
    .. note::
       This attribute is considered for downlink only when you set the
       :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to either **eNodeB Category Based** or
       **Band 46**.
    """

    SEM_AGGREGATED_MAXIMUM_POWER = 3178581
    r"""Specifies the aggregated maximum output power of all transmit antenna connectors. This value is expressed in dBm. Refer
    to the Section 6.6.3 of *3GPP 36.141* specification for more details.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0. Valid values are within 20, inclusive.
    
    .. note::
       This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
       attribute to **Downlink**, :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute to **Home Base
       Station**, and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **eNodeB Category
       Based**.
    """

    SEM_SUBBLOCK_INTEGRATION_BANDWIDTH = 3178577
    r"""Returns the integration bandwidth of the subblock. This value is expressed in Hz. Integration bandwidth is the span
    from the left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock.
    
    Use "subblock<*n*>" as the selector string to read this result.
    
    The default value is 0.
    """

    SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH = 3178578
    r"""Returns the aggregated channel bandwidth of a configured subblock. This value is expressed in Hz. The aggregated
    channel bandwidth is the sum of the subblock integration bandwidth and the guard bands on either side of the subblock
    integration bandwidth.
    
    Use "subblock<*n*>" as the selector string to read this result.
    
    The default value is 0.
    """

    SEM_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH = 3178501
    r"""Returns the integration bandwidth of a component carrier. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    The default value is 9 MHz.
    """

    SEM_COMPONENT_CARRIER_MAXIMUM_OUTPUT_POWER = 3178582
    r"""Specifies the maximum output power, P\ :sub:`max,c`\, per carrier that is used only to choose the limit table for
    Medium Range Base Station. For more details please refer to the section 6.6.3 of *3GPP 36.141* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0. Valid values are within 38, inclusive.
    
    .. note::
       This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
       attribute to **Downlink**, :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute to **Medium Range
       Base Station**, and :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **eNodeB Category
       Based**. When you set Bandwidth to  **200k**  the maximum output power, P\ :sub:`max,c`\, per carrier used to choose
       limit table and to calculate the mask.
    """

    SEM_NUMBER_OF_OFFSETS = 3178507
    r"""Specifies the number of SEM offset segments.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is 1.
    """

    SEM_OFFSET_START_FREQUENCY = 3178516
    r"""Specifies the start frequency of an offset segment relative to the
    :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
    is expressed in Hz.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 0.
    """

    SEM_OFFSET_STOP_FREQUENCY = 3178517
    r"""Specifies the stop frequency of an offset segment relative to the
    :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` edge (single carrier) or
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH` edge (multi-carrier). This value
    is expressed in Hz.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 1 MHz.
    """

    SEM_OFFSET_SIDEBAND = 3178515
    r"""Specifies whether the offset segment is present either on one side or on both sides of a carrier.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is **Both**.
    
    +--------------+---------------------------------------------------------------------------+
    | Name (Value) | Description                                                               |
    +==============+===========================================================================+
    | Neg (0)      | Configures a lower offset segment to the left of the leftmost carrier.    |
    +--------------+---------------------------------------------------------------------------+
    | Pos (1)      | Configures an upper offset segment to the right of the rightmost carrier. |
    +--------------+---------------------------------------------------------------------------+
    | Both (2)     | Configures both the negative and the positive offset segments.            |
    +--------------+---------------------------------------------------------------------------+
    """

    SEM_OFFSET_RBW_FILTER_BANDWIDTH = 3178519
    r"""Specifies the bandwidth of an RBW filter used to sweep an acquired offset segment. This value is expressed in Hz.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 30000 Hz.
    """

    SEM_OFFSET_RBW_FILTER_TYPE = 3178520
    r"""Specifies the shape of a digital RBW filter.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is **Gaussian**.
    
    +---------------+-----------------------------------------+
    | Name (Value)  | Description                             |
    +===============+=========================================+
    | FFT Based (0) | No RBW filtering is performed.          |
    +---------------+-----------------------------------------+
    | Gaussian (1)  | The RBW filter has a Gaussian response. |
    +---------------+-----------------------------------------+
    | Flat (2)      | The RBW filter has a flat response.     |
    +---------------+-----------------------------------------+
    """

    SEM_OFFSET_BANDWIDTH_INTEGRAL = 3178508
    r"""Specifies the resolution of a spectrum to compare with the spectral mask limits as an integer multiple of the RBW.
    
    When you set this attribute to a value greater than 1, the measurement acquires the spectrum with a narrow
    resolution and then processes it digitally to get a wider resolution that is equal to the product of a bandwidth
    integral and a RBW.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is 1.
    """

    SEM_OFFSET_LIMIT_FAIL_MASK = 3178509
    r"""Specifies the criteria to determine the measurement fail status.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is **Absolute**.
    
    .. note::
       When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**, all the values
       of limit fail mask are supported but when you set the Link Direction attribute to **Uplink**, the measurement
       internally sets the value of limit fail mask to **Absolute**.
    
    +-----------------+-------------------------------------------------------------------------------------------------------------+
    | Name (Value)    | Description                                                                                                 |
    +=================+=============================================================================================================+
    | Abs AND Rel (0) | Specifies the fail in measurement if the power in the segment exceeds both the absolute and relative masks. |
    +-----------------+-------------------------------------------------------------------------------------------------------------+
    | Abs OR Rel (1)  | Specifies the fail in measurement if the power in the segment exceeds either the absolute or relative mask. |
    +-----------------+-------------------------------------------------------------------------------------------------------------+
    | Absolute (2)    | Specifies the fail in measurement if the power in the segment exceeds the absolute mask.                    |
    +-----------------+-------------------------------------------------------------------------------------------------------------+
    | Relative (3)    | Specifies the fail in measurement if the power in the segment exceeds the relative mask.                    |
    +-----------------+-------------------------------------------------------------------------------------------------------------+
    """

    SEM_OFFSET_ABSOLUTE_LIMIT_START = 3178512
    r"""Specifies the absolute power limit corresponding to the beginning of an offset segment. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is -16.5.
    """

    SEM_OFFSET_ABSOLUTE_LIMIT_STOP = 3178513
    r"""Specifies the absolute power limit corresponding to the end of an offset segment. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is -16.5.
    """

    SEM_OFFSET_RELATIVE_LIMIT_START = 3178522
    r"""Specifies the relative power limit corresponding to the beginning of the offset segment. This value is expressed in dB.
    
    This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Downlink**.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is -51.5.
    """

    SEM_OFFSET_RELATIVE_LIMIT_STOP = 3178523
    r"""Specifies the relative power limit corresponding to the end of the offset segment. This value is expressed in dB.
    
    This attribute is considered only when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION`
    attribute to **Downlink**.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to configure or read this attribute.
    
    The default value is -58.5.
    """

    SEM_SWEEP_TIME_AUTO = 3178533
    r"""Specifies whether the measurement computes the sweep time.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+---------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                           |
    +==============+=======================================================================================+
    | False (0)    | The measurement uses the sweep time that you specify in the SEM Sweep Time attribute. |
    +--------------+---------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
    +--------------+---------------------------------------------------------------------------------------+
    """

    SEM_SWEEP_TIME_INTERVAL = 3178534
    r"""Specifies the sweep time when you set the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SWEEP_TIME_AUTO` attribute to
    **False**. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    SEM_AVERAGING_ENABLED = 3178527
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
    | True (1)     | The SEM measurement uses the value of the SEM Averaging Count attribute as the number of acquisitions over which the     |
    |              | SEM measurement is averaged.                                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_AVERAGING_COUNT = 3178526
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    SEM_AVERAGING_TYPE = 3178529
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
    | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.          |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.        |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    """

    SEM_AMPLITUDE_CORRECTION_TYPE = 3178583
    r"""Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
    the RF center frequency, or at the individual frequency bins. Use the
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

    SEM_ALL_TRACES_ENABLED = 3178535
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the SEM measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    SEM_NUMBER_OF_ANALYSIS_THREADS = 3178525
    r"""Specifies the maximum number of threads used for parallelism for the SEM measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    SEM_RESULTS_TOTAL_AGGREGATED_POWER = 3178536
    r"""Returns the sum of powers of all the subblocks. This value includes the power in the inter-carrier gap within a
    subblock, but it excludes power in the  inter-subblock gaps. This value is expressed in dBm.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    """

    SEM_RESULTS_MEASUREMENT_STATUS = 3178537
    r"""Returns the overall measurement status based on the standard mask type that you configure in the
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | Fail (0)     | Indicates that the measurement has failed. |
    +--------------+--------------------------------------------+
    | Pass (1)     | Indicates that the measurement has passed. |
    +--------------+--------------------------------------------+
    """

    SEM_RESULTS_SUBBLOCK_CENTER_FREQUENCY = 3178573
    r"""Returns the absolute center frequency of the subblock. This value is the center of the subblock integration bandwidth.
    Integration bandwidth is the span from the left edge of the leftmost carrier to the right edge of the rightmost carrier
    within the subblock. This value is expressed in Hz.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    SEM_RESULTS_SUBBLOCK_INTEGRATION_BANDWIDTH = 3178574
    r"""Returns the integration bandwidth of the subblock. Integration bandwidth is the span from left edge of the leftmost
    carrier to the right edge of the rightmost carrier within the subblock. This value is expressed in Hz.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    SEM_RESULTS_SUBBLOCK_POWER = 3178575
    r"""Returns the power measured over the integration bandwidth of the subblock. This value is expressed in dBm.
    
    Use "subblock<*n*>" as the selector string to read this result.
    """

    SEM_RESULTS_COMPONENT_CARRIER_ABSOLUTE_INTEGRATED_POWER = 3178541
    r"""Returns the sum of powers of all the frequency bins over the integration bandwidth of the carrier. This value is
    expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_COMPONENT_CARRIER_RELATIVE_INTEGRATED_POWER = 3178542
    r"""Returns the sum of powers of all the frequency bins over the integration bandwidth of the component carrier power
    relative to its subblock power. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_COMPONENT_CARRIER_ABSOLUTE_PEAK_POWER = 3178543
    r"""Returns the peak power in the component carrier. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_COMPONENT_CARRIER_PEAK_FREQUENCY = 3178544
    r"""Returns the frequency at which the peak power occurs in the component carrier. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MEASUREMENT_STATUS = 3178557
    r"""Indicates the measurement status based on the spectrum emission limits defined by the standard mask type that you
    configure in the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM mask.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | Fail (0)     | Indicates that the measurement has failed. |
    +--------------+--------------------------------------------+
    | Pass (1)     | Indicates that the measurement has passed. |
    +--------------+--------------------------------------------+
    """

    SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_INTEGRATED_POWER = 3178548
    r"""Returns the lower (negative) offset segment power. For the intra-band non-contiguous type of carrier aggregation, the
    offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
    specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
    offset segment is discarded, a NaN is returned. This value is expressed in dBm.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_RELATIVE_INTEGRATED_POWER = 3178549
    r"""Returns the power in the lower (negative) offset segment relative to the total aggregated power.  For the intra-band
    non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
    overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
    performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
    in dB.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_PEAK_POWER = 3178550
    r"""Returns the peak power in the lower (negative) offset segment.  For the intra-band non-contiguous type of carrier
    aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
    *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
    segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_RELATIVE_PEAK_POWER = 3178551
    r"""Returns the peak power in the lower (negative) offset segment relative to the total aggregated power.  For the
    intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the
    offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the
    measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This
    value is expressed in dB.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_PEAK_FREQUENCY = 3178552
    r"""Returns the frequency at which the peak power occurs in the lower (negative) offset segment. For the intra-band
    non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
    overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
    performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
    in Hz.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN = 3178553
    r"""Returns the margin from the standard-defined absolute limit mask for the lower (negative) offset. Margin is defined as
    the minimum difference between the limit mask and the spectrum. For the intra-band non-contiguous type of carrier
    aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
    *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
    segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dB.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_ABSOLUTE_POWER = 3178554
    r"""Returns the power at which the margin occurs in the lower (negative) offset segment. For the intra-band non-contiguous
    type of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as
    defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the
    updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_RELATIVE_POWER = 3178555
    r"""Returns the power at which the margin occurs in the lower (negative) offset segment relative to the total aggregated
    power. For the intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded
    based on the offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is
    truncated, the measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is
    returned. This value is expressed in dB.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_FREQUENCY = 3178556
    r"""Returns the frequency at which the margin occurs in the lower (negative) offset. For the intra-band non-contiguous type
    of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined
    in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated
    offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in Hz.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MEASUREMENT_STATUS = 3178570
    r"""Returns the measurement status based on the user-configured standard measurement limits and the failure criteria
    specified by Limit Fail Mask for the upper (positive) offset. For intra-band non-contiguous case, the offset segment
    may be truncated or discarded based on offset overlap rules defined in the *3GPP TS 36.521* specification. If the
    offset segment is truncated, the measurement is performed on the updated offset segment. If the offset segment is
    discarded, a NaN is returned.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | Fail (0)     | Indicates that the measurement has failed. |
    +--------------+--------------------------------------------+
    | Pass (1)     | Indicates that the measurement has passed. |
    +--------------+--------------------------------------------+
    """

    SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_INTEGRATED_POWER = 3178561
    r"""Returns the upper (positive) offset segment power. For the intra-band non-contiguous type of carrier aggregation, the
    offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
    specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
    offset segment is discarded, a NaN is returned. This value is expressed in dBm.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_RELATIVE_INTEGRATED_POWER = 3178562
    r"""Returns the power in the upper (positive) offset segment relative to the total aggregated power.
    
    For the intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded
    based on the offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is
    truncated, the measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is
    returned. This value is expressed in dB.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    """

    SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_PEAK_POWER = 3178563
    r"""Returns the power in the upper (positive) offset segment. For the intra-band non-contiguous type of carrier
    aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined in the
    *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated offset
    segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_RELATIVE_PEAK_POWER = 3178564
    r"""Returns the peak power in the upper (positive) offset segment relative to the total aggregated power. For the
    intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the
    offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the
    measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This
    value is expressed in dB.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_PEAK_FREQUENCY = 3178565
    r"""Returns the frequency at which the peak power occurs in the upper (positive) offset segment.  For the intra-band
    non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded based on the offset
    overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is
    performed on the updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed
    in Hz.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN = 3178566
    r"""Returns the margin from the absolute limit mask for the upper (positive) offset. The Margin is defined as the minimum
    difference between the limit mask and the spectrum. For the intra-band non-contiguous type of carrier aggregation, the
    offset segment may be truncated or discarded based on the offset overlap rules, as defined in the *3GPP TS 36.521*
    specification. If the offset segment is truncated, the measurement is performed on the updated offset segment. If the
    offset segment is discarded, a NaN is returned. This value is expressed in Hz.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_ABSOLUTE_POWER = 3178567
    r"""Returns the power at which the margin occurs in the upper (positive) offset segment. For the intra-band non-contiguous
    type of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as
    defined in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the
    updated offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in dBm.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_RELATIVE_POWER = 3178568
    r"""Returns the power at which the margin occurs in the upper (positive) offset segment relative to the total aggregated
    power. For the intra-band non-contiguous type of carrier aggregation, the offset segment may be truncated or discarded
    based on the offset overlap rules, as defined in the *3GPP TS 36.521* specification. If the offset segment is
    truncated, the measurement is performed on the updated offset segment. If the offset segment is discarded, a NaN is
    returned. This value is expressed in dB.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_FREQUENCY = 3178569
    r"""Returns the frequency at which the margin occurs in the upper (positive) offset. For the intra-band non-contiguous type
    of carrier aggregation, the offset segment may be truncated or discarded based on the offset overlap rules, as defined
    in the *3GPP TS 36.521* specification. If the offset segment is truncated, the measurement is performed on the updated
    offset segment. If the offset segment is discarded, a NaN is returned. This value is expressed in Hz.
    
    Refer to the `LTE Uplink Spectral Emission Mask
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-uplink-spectral-emission-mask.html>`_ and `LTE Downlink
    Spectral Emission Mask <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-downlink-spectral-emission-mask.html>`_
    topics for more information about SEM offsets.
    
    Use "offset<*k*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    PVT_MEASUREMENT_ENABLED = 3182592
    r"""Specifies whether to enable the power versus time (PVT) measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    PVT_MEASUREMENT_METHOD = 3182594
    r"""Specifies the method for performing the power versus time (PVT) measurement.
    
    Refer to the `LTE PVT (Power Vs Time) Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about multi
    acquisition PVT.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Normal**.
    
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)      | Description                                                                                                              |
    +===================+==========================================================================================================================+
    | Normal (0)        | The measurement is performed using a single acquisition. Use this method when a high dynamic range is not required.      |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Dynamic Range (1) | The measurement is performed using two acquisitions. Use this method when a higher dynamic range is desirable over the   |
    |                   | measurement speed. Supported Devices: PXIe-5644/5645/5646, PXIe-5840/5841/5842/5860                                      |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    PVT_AVERAGING_ENABLED = 3182599
    r"""Specifies whether to enable averaging for the power versus time (PVT) measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The PVT measurement uses the value of the PVT Averaging Count attribute as the number of acquisitions over which the     |
    |              | PVT measurement is averaged.                                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    PVT_AVERAGING_COUNT = 3182601
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.PVT_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    PVT_AVERAGING_TYPE = 3182602
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for the power
    versus time (PVT) measurement.
    
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
    """

    PVT_OFF_POWER_EXCLUSION_BEFORE = 3182613
    r"""Specifies the time excluded from the Off region before the burst. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    Refer to the `LTE PVT (Power Vs Time) Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about OFF
    power exclusion.
    
    The default value is 0.
    """

    PVT_OFF_POWER_EXCLUSION_AFTER = 3182614
    r"""Specifies the time excluded from the Off region after the burst. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    Refer to the `LTE PVT (Power Vs Time) Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about OFF
    power exclusion.
    
    The default value is 0.
    """

    PVT_ALL_TRACES_ENABLED = 3182603
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the power versus time (PVT)
    measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    PVT_NUMBER_OF_ANALYSIS_THREADS = 3182604
    r"""Specifies the maximum number of threads used for parallelism for the power versus time (PVT) measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    PVT_RESULTS_MEASUREMENT_STATUS = 3182606
    r"""Returns the measurement status indicating whether the power before and after the burst is within the standard defined
    limit.
    
    Refer to the `LTE PVT (Power Vs Time) Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about
    measurement status.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | Fail (0)     | Indicates that the measurement has failed. |
    +--------------+--------------------------------------------+
    | Pass (1)     | Indicates that the measurement has passed. |
    +--------------+--------------------------------------------+
    """

    PVT_RESULTS_MEAN_ABSOLUTE_OFF_POWER_BEFORE = 3182608
    r"""Returns the mean power in the segment before the captured burst. The segment is defined as one subframe prior to the
    burst for the FDD mode and 10 SC-FDMA symbols prior to the burst for the TDD mode. This value is expressed in dBm.
    
    Refer to the `LTE PVT (Power Vs Time) Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about OFF
    Power.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    PVT_RESULTS_MEAN_ABSOLUTE_OFF_POWER_AFTER = 3182609
    r"""Returns the mean power in the segment after the captured burst. This value is expressed in dBm. The segment is defined
    as one subframe long, excluding a transient period of 20 micro seconds at the beginning.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    
    Refer to the `LTE PVT (Power Vs Time) Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/lte-power-vs-time.html>`_ topic for more information about OFF
    Power.
    """

    PVT_RESULTS_MEAN_ABSOLUTE_ON_POWER = 3182610
    r"""Returns the average power of the subframes within the captured burst. This value is expressed in dBm. The average power
    excludes the transient period of 20 micro seconds at the beginning.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    PVT_RESULTS_BURST_WIDTH = 3182612
    r"""Returns the width of the captured burst. This value is expressed in seconds.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read this result.
    """

    SLOTPHASE_MEASUREMENT_ENABLED = 3186688
    r"""Specifies whether to enable the SlotPhase measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    SLOTPHASE_SYNCHRONIZATION_MODE = 3186694
    r"""Specifies whether the measurement is performed from the frame or the slot boundary.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Slot**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Frame (0)    | The frame boundary in the acquired signal is detected, and the measurement is performed over the number of slots         |
    |              | specified by the SlotPhase Meas Length attribute, starting at the offset from the boundary specified by the SlotPhase    |
    |              | Meas Offset attribute. When the Trigger Type attribute is set to Digital, the measurement expects a trigger at the       |
    |              | frame boundary.                                                                                                          |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Slot (1)     | The slot boundary in the acquired signal is detected, and the measurement is performed over the number of slots          |
    |              | specified by the SlotPhase Meas Length attribute, starting at the offset from the boundary specified by the SlotPhase    |
    |              | Meas Offset attribute. When the Trigger Type attribute is set to Digital, the measurement expects a trigger at any slot  |
    |              | boundary.                                                                                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SLOTPHASE_MEASUREMENT_OFFSET = 3186690
    r"""Specifies the measurement offset to skip from the synchronization boundary. This value is expressed in slots. The
    synchronization boundary is specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_SYNCHRONIZATION_MODE` attribute.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0. Valid values are 0 to 19, inclusive.
    """

    SLOTPHASE_MEASUREMENT_LENGTH = 3186691
    r"""Specifies the number of slots to be measured. This value is expressed in slots.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 20.
    """

    SLOTPHASE_EXCLUSION_PERIOD_ENABLED = 3186695
    r"""Specifies whether to exclude some portions of the slots when calculating the phase. This attribute is valid only when
    there is a power change at the slot boundary. Refer to section 6.5.2.1A of the *3GPP 36.521-1* specification for more
    information about the exclusion.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | Phase is calculated on complete slots.                                                                                   |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | Phase is calculated on truncated slots. The power changes at the slot boundaries are detected by the measurement, and    |
    |              | the defined 3GPP specification period is excluded from the slots being measured.                                         |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SLOTPHASE_COMMON_CLOCK_SOURCE_ENABLED = 3186696
    r"""Specifies whether the same Reference Clock is used for local oscillator and the digital-to-analog converter. When the
    same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------+
    | Name (Value) | Description                                                        |
    +==============+====================================================================+
    | False (0)    | The Sample Clock error is estimated independently.                 |
    +--------------+--------------------------------------------------------------------+
    | True (1)     | The Sample Clock error is estimated from carrier frequency offset. |
    +--------------+--------------------------------------------------------------------+
    """

    SLOTPHASE_SPECTRUM_INVERTED = 3186697
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

    SLOTPHASE_ALL_TRACES_ENABLED = 3186699
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the SlotPhase measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    SLOTPHASE_RESULTS_MAXIMUM_PHASE_DISCONTINUITY = 3186708
    r"""Returns the maximum value of phase difference at the slot boundaries within the
    :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH`. This values is expressed in degrees.
    
    Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>"  as the selector string to read this attribute.
    """

    SLOTPOWER_MEASUREMENT_ENABLED = 3190784
    r"""Specifies whether to enable the SlotPower measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    SLOTPOWER_MEASUREMENT_OFFSET = 3190786
    r"""Specifies the measurement offset to skip from the frame boundary or the marker (external trigger) location. This value
    is expressed in subframe.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    SLOTPOWER_MEASUREMENT_LENGTH = 3190787
    r"""Specifies the number of subframes to be measured. This value is expressed in subframe.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    SLOTPOWER_COMMON_CLOCK_SOURCE_ENABLED = 3190789
    r"""Specifies whether the same Reference Clock is used for the local oscillator and the digital-to-analog converter in the
    transmitter. When the same Reference Clock is used, the carrier frequency offset is proportional to Sample Clock error.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------+
    | Name (Value) | Description                                                        |
    +==============+====================================================================+
    | False (0)    | The Sample Clock error is estimated independently.                 |
    +--------------+--------------------------------------------------------------------+
    | True (1)     | The Sample Clock error is estimated from carrier frequency offset. |
    +--------------+--------------------------------------------------------------------+
    """

    SLOTPOWER_SPECTRUM_INVERTED = 3190790
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

    SLOTPOWER_ALL_TRACES_ENABLED = 3190794
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the SlotPower measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    TXP_MEASUREMENT_ENABLED = 3203072
    r"""Specifies whether to enable the Transmit Power (TXP) measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    TXP_MEASUREMENT_OFFSET = 3203074
    r"""Specifies the measurement offset to skip from the start of acquired waveform for TXP measurement. This value is
    expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    TXP_MEASUREMENT_INTERVAL = 3203075
    r"""Specifies the measurement interval. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    TXP_AVERAGING_ENABLED = 3203076
    r"""Specifies whether to enable averaging for TXP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                     |
    +==============+=================================================================================================================+
    | False (0)    | The number of acquisitions is 1.                                                                                |
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the Averaging Count for the number of acquisitions over which the measurement is averaged. |
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    """

    TXP_AVERAGING_COUNT = 3203077
    r"""Specifies the number of acquisitions used for averaging when
    :py:attr:`~nirfmxlte.attributes.AttributeID.TXP_AVERAGING_ENABLED` is **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    TXP_ALL_TRACES_ENABLED = 3203079
    r"""Enables the traces to be stored and retrieved after the TXP measurement is performed.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is False.
    """

    TXP_NUMBER_OF_ANALYSIS_THREADS = 3203080
    r"""Specifies the maximum number of threads used for parallelism inside TXP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The number of threads must range from 1 to the number of physical cores. The default value is 1.
    
    The number of threads set used in calculations is not guaranteed. The actual number of threads used depends on
    the problem size, system resources, data availability, and other considerations.
    """

    TXP_RESULTS_AVERAGE_POWER_MEAN = 3203082
    r"""Returns the average power of the acquired signal.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
    returns the mean of the average power computed for each averaging count.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    TXP_RESULTS_PEAK_POWER_MAXIMUM = 3203083
    r"""Returns the peak power of the acquired signal.
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
    returns the max of the peak power computed for each averaging count.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    AUTO_LEVEL_INITIAL_REFERENCE_LEVEL = 3198976
    r"""Specifies the initial reference level that the :py:meth:`auto_level` method uses to estimate the peak power of the
    input signal. This value is expressed in dBm.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 30.
    """

    ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED = 3198977
    r"""Specifies whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
    oscillator (LO) to be placed at different position than you configured.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    Refer to the `Acquisition Bandwidth Optimization Enabled
    <https://www.ni.com/docs/en-US/bundle/rfmx-lte/page/acquisition-bandwidth-optimization.html>`_ topic for more
    information.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | RFmx does not optimize acquisition bandwidth and will be based on the Nyquist criterion. The value of the acquisition    |
    |              | center frequency is the same as the value of the Center Frequency that you configure.                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | RFmx positions the acquisition center frequency to acquire the least bandwidth based on the configuration and span       |
    |              | needed for the measurement. This helps in reducing the amount of data to process for the measurement, thus improving     |
    |              | the speed. However this might cause the LO to be positioned at a non-dc subcarrier position, hence the measurement       |
    |              | sensitive to it should have this attribute disabled.                                                                     |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    TRANSMITTER_ARCHITECTURE = 3198978
    r"""Specifies the RF architecture at the transmitter in case of a multicarrier. 3GPP defines different options, each
    component carriers within a subblock can have separate LO or one common LO for an entire subblock. Based upon the
    selected option, the additional results are calculated.
    
    The measurement ignores this attribute when you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **LO per Component Carrier**.
    
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)                 | Description                                                                                                              |
    +==============================+==========================================================================================================================+
    | LO per Component Carrier (0) | IQ impairments and In-band emission are calculated per component carrier.                                                |
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | LO per Subblock (1)          | Additional subblock based results such as Subblock IQ Offset and Subblock In band emission are calculated apart from     |
    |                              | per carrier results.                                                                                                     |
    +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    LIMITED_CONFIGURATION_CHANGE = 3198979
    r"""Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.
    
    If your test system performs the same measurement at different selected ports, multiple frequencies and/or
    power levels repeatedly, enabling this attribute can help achieve faster measurements. When you set this attribute to a
    value other than **Disabled**, RFmx will use an optimized code path and skip some checks. Because RFmx skips some
    checks when you use this attribute, you need to be aware of the limitations of this feature, which are listed in the
    `Limitations of the Limited Configuration Change Property
    <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.
    
    You can also use this attribute to lock a specific instrument configuration for a signal so that every time
    that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.
    
    NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
    configurations for each measurement configuration in your test program and set this attribute to a value other than
    **Disabled** for one or more of the named signal configurations. This allows RFmx to pre-compute the acquisition
    settings for your measurement configurations and re-use the precomputed settings each time you initiate the
    measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
    in your test program during test sequence initialization and do not change any RFmxInstr or personality attributes
    while testing each device under test. RFmx automatically optimizes that use case.
    
    Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
    need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
    Selector String topic for information about the string syntax for named signals.
    
    The default value is **Disabled**.
    
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)                           | Description                                                                                                              |
    +========================================+==========================================================================================================================+
    | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
    |                                        | attributes will be applied during RFmx Commit.                                                                           |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | No Change (1)                          | Signal configuration is locked after the first Commit of the named signal configuration. Any configuration change        |
    |                                        | thereafter either in RFmxInstr attributes or personality attributes will not be considered by subsequent RFmx Commits    |
    |                                        | or Initiates of this signal.                                                                                             |
    |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
    |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
    |                                        | about the limitations of using this mode.                                                                                |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Frequency (2)                          | Signal configuration, other than center frequency and external attenuation, is locked after first Commit of the named    |
    |                                        | signal configuration. Thereafter, only the Center Frequency and External Attenuation attribute value changes will be     |
    |                                        | considered by subsequent driver Commits or Initiates of this signal.                                                     |
    |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
    |                                        | using this mode.                                                                                                         |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Reference Level (3)                    | Signal configuration, other than the reference level, is locked after first Commit of the named signal configuration.    |
    |                                        | Thereafter only the Reference Level attribute value change will be considered by subsequent driver Commits or Initiates  |
    |                                        | of this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends that you set the IQ    |
    |                                        | Power Edge Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference        |
    |                                        | level. Refer to the Limitations of the Limited Configuration Change Property topic for more details about the            |
    |                                        | limitations of using this mode.                                                                                          |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, and external attenuation, is locked after first      |
    |                                        | Commit of the named signal configuration. Thereafter only Center Frequency, Reference Level, and External Attenuation    |
    |                                        | attribute value changes will be considered by subsequent driver Commits or Initiates of this signal. If you have         |
    |                                        | configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power Edge Level Type attribute to  |
    |                                        | Relative so that the trigger level is automatically adjusted as you adjust the reference level. Refer to the             |
    |                                        | Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this      |
    |                                        | mode.                                                                                                                    |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than Selected Ports, Center frequency, Reference level, External attenuation, and RFmxInstr  |
    |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
    |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
    |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
    |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type attribute to Relative so that the trigger level is           |
    |                                        | automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change   |
    |                                        | Property topic for more details about the limitations of using this mode.                                                |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    CENTER_FREQUENCY_FOR_LIMITS = 3198980
    r"""Specifies the frequency that determines the SEM mask, IBE limits, and spectral flatness ranges. If you do not set a
    value for this attribute, the measurement internally uses the
    :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` for determining SEM mask, IBE limits, and spectral
    flatness ranges. This value is expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    RESULT_FETCH_TIMEOUT = 3194880
    r"""Specifies the time to wait before results are available in the RFmxLTE Attribute. This value is expressed in seconds.
    Set this value to a time longer than expected for fetching the measurement. A value of -1 specifies that the  RFmx
    Attribute waits until the measurement is complete.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """
