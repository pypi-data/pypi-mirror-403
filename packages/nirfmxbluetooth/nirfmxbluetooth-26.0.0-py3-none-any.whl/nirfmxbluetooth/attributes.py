"""attributes.py - Contains the ID of all attributes belongs to the module."""

from enum import Enum


class AttributeID(Enum):
    """This enum class contains the ID of all attributes belongs to the module."""

    SELECTED_PORTS = 11538429
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

    CENTER_FREQUENCY = 11534337
    r"""Specifies the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
    signal analyzer tunes to this frequency.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is hardware dependent. The default value for the devices PXIe-5645/5820 is 0 Hz. The default
    value for devices PXIe-5644/5646/5840/5663/5663E/5665/5668R is 2.402 GHz.
    """

    REFERENCE_LEVEL = 11534338
    r"""Specifies the reference level that represents the maximum expected power of the RF input signal. This value is
    expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    EXTERNAL_ATTENUATION = 11534339
    r"""Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
    expressed in dB.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    For more information about attenuation, refer to the *Attenuation and Signal Levels* topic for your device in
    the *NI RF Vector Signal Analyzers Help*.
    
    The default value is 0.
    """

    REFERENCE_LEVEL_HEADROOM = 11538428
    r"""Specifies the margin RFmx adds to the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
    margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.
    
    RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
    power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
    power of the signal precisely or previously included the margin in the Reference Level, you could improve the
    signal-to-noise ratio by reducing the Reference Level Headroom.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    **Supported devices: **PXIe-5668R, PXIe-5830/5831/5832/5840/5841/5842/5860.
    
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

    TRIGGER_TYPE = 11534340
    r"""Specifies the type of trigger to be used for signal acquisition.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **IQ Power Edge**.
    
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)      | Description                                                                                                              |
    +===================+==========================================================================================================================+
    | None (0)          | No reference trigger is used for signal acquisition.                                                                     |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Digital Edge (1)  | A digital-edge trigger is used for signal acquisition. The source of the digital edge is specified using the Digital     |
    |                   | Edge Source attribute.                                                                                                   |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | IQ Power Edge (2) | An I/Q power-edge trigger is used for signal acquisition, which is configured using the IQ Power Edge Slope attribute.   |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Software (3)      | A software trigger is used for signal acquisition.                                                                       |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    DIGITAL_EDGE_TRIGGER_SOURCE = 11534341
    r"""Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default of this attribute is hardware dependent.
    """

    DIGITAL_EDGE_TRIGGER_EDGE = 11534342
    r"""Specifies the active edge for the trigger. This attribute is valid only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.
    
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

    IQ_POWER_EDGE_TRIGGER_SOURCE = 11534343
    r"""Specifies the channel from which the device monitors the trigger. This attribute is valid only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    IQ_POWER_EDGE_TRIGGER_LEVEL = 11534344
    r"""Specifies the power level at which the device triggers. The device asserts the trigger when the signal exceeds the
    level specified by the value of this parameter, taking into consideration the specified slope.
    
    This value is expressed in dB when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in
    dBm when you set the IQ Power Edge Level Type attribute to **Absolute**. This attribute is valid only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is hardware dependent.
    """

    IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE = 11538431
    r"""Specifies the reference for the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL`
    attribute. The IQ Power Edge Level Type attribute is used only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
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

    IQ_POWER_EDGE_TRIGGER_SLOPE = 11534345
    r"""Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
    asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
    used only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power
    Edge**.
    
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

    TRIGGER_DELAY = 11534346
    r"""Specifies the trigger delay time. This value is expressed in seconds.
    
    If the delay is negative, the measurement acquires pretrigger samples. If the delay is positive, the
    measurement acquires posttrigger samples.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    TRIGGER_MINIMUM_QUIET_TIME_MODE = 11534347
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

    TRIGGER_MINIMUM_QUIET_TIME_DURATION = 11534348
    r"""Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
    trigger. This value is expressed in seconds.
    
    If you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to
    **Rising Slope**, the signal is quiet below the trigger level. If you set the IQ Power Edge Slope attribute to
    **Falling Slope**, the signal is quiet above the trigger level.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    PACKET_TYPE = 11534349
    r"""Specifies the type of the Bluetooth packet to be measured.
    
    In this document, packet type is sometimes referred to by the Bluetooth physical layer (PHY) it belongs to.
    Supported Bluetooth physical layers are basic rate (BR), enhanced data rate (EDR), low energy (LE) and low energy -
    channel sounding (LE-CS).
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **DH1**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | DH1 (0)      | Specifies that the packet type is DH1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.2, Part B,      |
    |              | Volume 2 of the Bluetooth Core Specification v6.0 for more information about this packet.                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | DH3 (1)      | Specifies that the packet type is DH3. The packet belongs to BR PHY. Refer to section 6.5.4.4, Part B, Volume 2 of the   |
    |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | DH5 (2)      | Specifies that the packet type is DH5. The packet belongs to BR PHY. Refer to section 6.5.4.6, Part B, Volume 2 of the   |
    |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | DM1 (3)      | Specifies that the packet type is DM1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.1, Part B,      |
    |              | Volume 2 of the Bluetooth Core Specification v6.0 for more information about this packet.                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | DM3 (4)      | Specifies that the packet type is DM3. The packet belongs to BR PHY. Refer to section 6.5.4.3, Part B, Volume 2 of the   |
    |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | DM5 (5)      | Specifies that the packet type is DM5. The packet belongs to BR PHY. Refer to section 6.5.4.5, Part B, Volume 2 of the   |
    |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 2-DH1 (6)    | Specifies that the packet type is 2-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.8, Part B, Volume 2 of    |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 2-DH3 (7)    | Specifies that the packet type is 2-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.9, Part B, Volume 2 of    |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 2-DH5 (8)    | Specifies that the packet type is 2-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.10, Part B, Volume 2 of   |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 3-DH1 (9)    | Specifies that the packet type is 3-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.11, Part B, Volume 2 of   |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 3-DH3 (10)   | Specifies that the packet type is 3-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.12, Part B, Volume 2 of   |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 3-DH5 (11)   | Specifies that the packet type is 3-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.13, Part B, Volume 2 of   |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 2-EV3 (12)   | Specifies that the packet type is 2-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.4, Part B, Volume 2 of    |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 2-EV5 (13)   | Specifies that the packet type is 2-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.5, Part B, Volume 2 of    |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 3-EV3 (14)   | Specifies that the packet type is 3-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.6, Part B, Volume 2 of    |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | 3-EV5 (15)   | Specifies that the packet type is 3-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.7, Part B, Volume 2 of    |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | LE (16)      | Specifies that the packet type is LE. The packet belongs to LE PHY. Refer to sections 2.1 and 2.2, Part B, Volume 6 of   |
    |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | LE-CS (17)   | Specifies that the packet type is LE-CS. The packet belongs to LE-CS PHY. Refer to Section 2, Part H, Volume 6 of the    |
    |              | Bluetooth Specification v6.0 for more information about this packet                                                      |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | LE-HDT (18)  | Specifies that the packet type is LE-HDT. The packet belongs to LE-HDT PHY.                                              |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    DATA_RATE = 11534350
    r"""Specifies the data rate of the LE, LE-CS or LE-HDT packet transmitted by the device under test (DUT). This value is
    expressed in bps. This attribute is applicable only to LE, LE-CS or LE-HDT packet type.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **1M**.
    """

    BANDWIDTH_BIT_PERIOD_PRODUCT = 11534388
    r"""Specifies the bandwidth bit period product of GFSK modulation for LE-CS packet type.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.5.
    """

    BD_ADDRESS_LAP = 11534351
    r"""Specifies the 24-bit lower address part (LAP) of the bluetooth device address (BD_ADDR).
    
    This value is used to generate the sync word if you set the burst synchronization type attribute in TXP, ACP,
    or ModAcc measurements to **Sync Word**. This attribute is applicable only to BR and EDR packet types.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    ACCESS_ADDRESS = 11534353
    r"""Specifies the 32-bit LE access address.
    
    This value is used to synchronize to the start of the packet if you set the burst synchronization type
    attribute in TXP, ACP, or ModAcc measurements to **Sync Word** and the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE** or **LE-CS**.
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0x71764129 as specified by the bluetooth standard.
    """

    PAYLOAD_BIT_PATTERN = 11534354
    r"""Specifies the bit pattern present in the payload of the packet. This value is used to determine the set of ModAcc
    measurements to be performed.
    
    The following table shows the measurements applicable for different Payload Bit Pattern:
    
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    | Bluetooth PHY | Data Rate | Standard                                                                           | 11110000                                                                                                     | 10101010                   |
    +===============+===========+====================================================================================+==============================================================================================================+============================+
    | BR            | NA        | Error                                                                              | df1                                                                                                          | df2 and BR frequency error |
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    | EDR           | NA        | DEVM (The measurement considers PN9 as payload pattern)                            | Error                                                                                                        | Error                      |
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    | LE            | 1 Mbps    | Error                                                                              | df1 and LE frequency errors on the constant tone extension (CTE) field within the direction finding packets. | df2 and LE frequency error |
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    | LE            | 2 Mbps    | Error                                                                              | df1 and LE frequency errors on the constant tone extension (CTE) field within the direction finding packets. | df2 and LE frequency error |
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    | LE            | 125 kbps  | df1 and LE frequency error (The measurement considers 11111111 as payload pattern) | Error                                                                                                        | Error                      |
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    | LE            | 500 kbps  | df2 and LE frequency error (The measurement considers 11111111 as payload pattern) | Error                                                                                                        | Error                      |
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    | LE-CS         | 1 Mbps    | Error                                                                              | df1                                                                                                          | df2 and LE frequency error |
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    | LE-CS         | 2 Mbps    | Error                                                                              | df1                                                                                                          | df2 and LE frequency error |
    +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Standard Defined**.
    
    +----------------------+-------------------------------------------------------------+
    | Name (Value)         | Description                                                 |
    +======================+=============================================================+
    | Standard Defined (0) | Specifies that the payload bit pattern is Standard Defined. |
    +----------------------+-------------------------------------------------------------+
    | 11110000 (1)         | Specifies that the payload bit pattern is 11110000.         |
    +----------------------+-------------------------------------------------------------+
    | 10101010 (2)         | Specifies that the payload bit pattern is 10101010.         |
    +----------------------+-------------------------------------------------------------+
    """

    PAYLOAD_LENGTH_MODE = 11534355
    r"""Specifies the payload length mode of the signal to be measured. The payload length mode and
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH` attributes decide the length of the payload to be
    used for measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Auto**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Manual (0)   | Enables the value specified by the Payload Length attribute. The acquisition and measurement durations will be decided   |
    |              | based on this value.                                                                                                     |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Auto (1)     | Enables the standard defined maximum payload length for BR, EDR, LE and LE-CS packet, and the maximum payload zone       |
    |              | length for LE-HDT packet. If this attribute is set to Auto, the maximum standard defined payload length or payload zone  |
    |              | length for the selected Packet Type is chosen. The maximum payload length a device under test (DUT) can generate varies  |
    |              | from 37 to 255 bytes for LE packet, and the maximum payload zone length varies from 514 to 33020 bytes for LE-HDT        |
    |              | packet. When you set the payload length mode to Auto, RFmx chooses 37 bytes for LE packet and 514 bytes for LE-HDT       |
    |              | packet.                                                                                                                  |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    PAYLOAD_LENGTH = 11534356
    r"""Specifies the payload length of BR, EDR, LE and LE-CS packet, and the payload zone length of LE-HDT packet, in bytes.
    This attribute is applicable only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH_MODE` attribute to **Manual**. This attribute returns
    the payload length or payload zone length used for measurement if you set the Payload Length Mode attribute to
    **Auto**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    DIRECTION_FINDING_MODE = 11534380
    r"""Specifies the mode of direction finding.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Disabled**.
    
    +------------------------+----------------------------------------------------------------------------------------+
    | Name (Value)           | Description                                                                            |
    +========================+========================================================================================+
    | Disabled (0)           | Specifies that the LE packet does not have fields required for direction finding.      |
    +------------------------+----------------------------------------------------------------------------------------+
    | Angle of Arrival (1)   | Specifies that the LE packets uses the Angle of Arrival method of direction finding.   |
    +------------------------+----------------------------------------------------------------------------------------+
    | Angle of Departure (2) | Specifies that the LE packets uses the Angle of Departure method of direction finding. |
    +------------------------+----------------------------------------------------------------------------------------+
    """

    CTE_LENGTH = 11534381
    r"""Specifies the length of the constant tone extension (CTE) field in the generated signal. This value is expressed in
    seconds. This attribute is applicable only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to either **Angle of Arrival** or
    **Angle of Departure**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 160 microseconds.
    """

    CTE_SLOT_DURATION = 11534382
    r"""Specifies the length of the switching slots and transmit slots in the constant tone extension field in the generated
    signal. This attribute is applicable only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Arrival** or **Angle
    of Departure**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1u.
    """

    CTE_NUMBER_OF_TRANSMIT_SLOTS = 11534383
    r"""Returns the number of transmit slots in the constant time extension portion of the generated LE packet. This attribute
    is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute
    to **Angle of Arrival** or **Angle of Departure**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    CHANNEL_SOUNDING_PACKET_FORMAT = 11534384
    r"""Specifies the format of the Channel Sounding packet depending on the position and presence of SYNC and CS Tone fields.
    This attribute is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE`
    attribute to **LE-CS**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **SYNC**.
    
    +-------------------------+-----------------------------------------------------------------------------+
    | Name (Value)            | Description                                                                 |
    +=========================+=============================================================================+
    | SYNC (0)                | Specifies that the LE-CS packet contains only SYNC portion.                 |
    +-------------------------+-----------------------------------------------------------------------------+
    | CS Tone (1)             | Specifies that the LE-CS packet contains only CS Tone.                      |
    +-------------------------+-----------------------------------------------------------------------------+
    | CS Tone after SYNC (2)  | Specifies that the CS Tone portion is at the end of the LE-CS packet.       |
    +-------------------------+-----------------------------------------------------------------------------+
    | CS Tone before SYNC (3) | Specifies that the CS Tone portion is at the beginning of the LE-CS packet. |
    +-------------------------+-----------------------------------------------------------------------------+
    """

    CHANNEL_SOUNDING_SYNC_SEQUENCE = 11534385
    r"""Specifies the type of sequence present in the SYNC portion after trailer bits. This attribute is applicable only when
    you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
    **CS Tone**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **None**.
    
    +------------------------------+--------------------------------------------------------------------------------------------------------+
    | Name (Value)                 | Description                                                                                            |
    +==============================+========================================================================================================+
    | None (0)                     | Specifies that there is no optional sequence at the end of the SYNC portion of the LE-CS packet.       |
    +------------------------------+--------------------------------------------------------------------------------------------------------+
    | Sounding Sequence 32-bit (1) | Specifies that there is a 32-bit sounding sequence at the end of the SYNC portion of the LE-CS packet. |
    +------------------------------+--------------------------------------------------------------------------------------------------------+
    | Sounding Sequence 96-bit (2) | Specifies that there is a 96-bit sounding sequence at the end of the SYNC portion of the LE-CS packet. |
    +------------------------------+--------------------------------------------------------------------------------------------------------+
    | Payload Pattern (3)          | Specifies that the payload bit pattern is present at the end of the SYNC portion of the LE-CS packet.  |
    +------------------------------+--------------------------------------------------------------------------------------------------------+
    """

    CHANNEL_SOUNDING_PHASE_MEASUREMENT_PERIOD = 11534386
    r"""Specifies the Channel Sounding Phase Measurement Period for the LE-CS packet. This attribute is applicable only when
    you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
    **SYNC**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **10 us**.
    """

    CHANNEL_SOUNDING_TONE_EXTENSION_SLOT = 11534387
    r"""Specifies whether the tone extension slot transmission is enabled after CS Tone. This attribute is applicable only when
    you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
    **SYNC**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Disabled**.
    
    +--------------+------------------------------------------------------------------------+
    | Name (Value) | Description                                                            |
    +==============+========================================================================+
    | Disabled (0) | Specifies that there is no transmission in the CS Tone extension slot. |
    +--------------+------------------------------------------------------------------------+
    | Enabled (1)  | Specifies that there is transmission in the CS Tone extension slot.    |
    +--------------+------------------------------------------------------------------------+
    """

    CHANNEL_SOUNDING_NUMBER_OF_ANTENNA_PATH = 11534390
    r"""Specifies the number of antenna paths for the generated LE-CS packet. This attribute is applicable only when you set
    the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
    **SYNC**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **1**.
    """

    CHANNEL_SOUNDING_ANTENNA_SWITCH_TIME = 11534389
    r"""Specifies the Channel Sounding Antenna Switch Time for the LE-CS packet. This attribute is applicable only when you set
    the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
    **SYNC**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **0 us**.
    """

    ZADOFF_CHU_INDEX = 11534393
    r"""Specifies Zadoff-Chu Index for the Long Training Sequence in the preamble. Input to the Zadoff-Chu Index attribute must
    be in the range of [1 - 16]. This attribute is applicable only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **7**.
    """

    HIGH_DATA_THROUGHPUT_PACKET_FORMAT = 11534392
    r"""Specifies the Higher Data Throughput (HDT) packet format. This attribute is applicable only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Format0**.
    
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)     | Description                                                                                                              |
    +==================+==========================================================================================================================+
    | Short Format (0) | Specifies that the HDT packet format is Short Format. This packet consists of preamble and control header field.         |
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Format0 (1)      | Specifies that the HDT packet format is Format0. This packet consists of preamble, control header, PDU header and        |
    |                  | payload field. The maximum payload length is 510 bytes.                                                                  |
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Format1 (2)      | Specifies that the HDT packet format is Format1. This packet format is similar to the Format0 but its payload zone       |
    |                  | consists of multiple blocks and the maximum payload length per payload is 8191 bytes.                                    |
    +------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    VHDT_MODE_ENABLED = 11534400
    r"""+--------------+-------------+
    | Name (Value) | Description |
    +==============+=============+
    | False (0)    |             |
    +--------------+-------------+
    | True (1)     |             |
    +--------------+-------------+
    """

    NUMBER_OF_BLOCK_REPETITION_SEQUENCES = 11534401
    r"""
    """

    CHANNEL_NUMBER = 11534359
    r"""Specifies the RF channel number of the signal generated by the device under test (DUT), as defined in the bluetooth
    specification. This attribute is applicable when you enable the ACP measurement and when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    DETECTED_PACKET_TYPE = 11534361
    r"""Returns the packet type detected by the RFmxBluetooth Auto Detect Signal method. This attribute can be queried only after
    calling the RFmxBluetooth Auto Detect Signal method.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is **Unknown**.
    """

    DETECTED_DATA_RATE = 11534378
    r"""Returns the data rate detected by the RFmxBluetooth Auto Detect Signal method. This attribute returns a valid data rate only
    if the Detected Packet Type attribute returns LE. This attribute can be queried only after calling the RFmxBluetooth Auto
    Detect Signal method.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is **Not Applicable**.
    """

    DETECTED_PAYLOAD_LENGTH = 11534379
    r"""Returns the payload length detected by the RFmxBluetooth Auto Detect Signal method. This attribute can be queried only after
    calling the RFmxBluetooth Auto Detect Signal method.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is -1.
    """

    MODACC_MEASUREMENT_ENABLED = 11550720
    r"""Specifies whether to enable the ModAcc measurements. You can use this attribute to determine the modulation quality of
    the bluetooth transmitter.
    
    You can perform the following sub-measurements when ModAcc measurement is enabled:
    <ul><li>
    DEVM, on EDR packets</li>
    <li>
    df1, on BR and LE packets</li>
    <li>
    df2, on BR and LE packets</li>
    <li>
    Frequency Error, on BR, EDR, LE and LE-CS packets</li></ul>
    
    The listed sub-measurements are enabled or disabled based on the value of the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_BIT_PATTERN` attribute.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is FALSE.
    """

    MODACC_BURST_SYNCHRONIZATION_TYPE = 11550763
    r"""Specifies the type of synchronization used for detecting the start of packet in ModAcc measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Preamble**.
    
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)  | Description                                                                                                              |
    +===============+==========================================================================================================================+
    | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.                       |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Preamble (1)  | Specifies that the measurement uses the preamble field to detect the start of the packet.                                |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Sync Word (2) | Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to      |
    |               | detect the start of the packet. For BR /EDR packets, the sync word is derived from the BD Address LAP attribute.         |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_IQ_ORIGIN_OFFSET_CORRECTION_ENABLED = 11550723
    r"""Specifies whether to enable the I/Q origin offset correction for EDR and LE-HDT packets. If you set this attribute to
    **True**, the DEVM and EVM results are computed after correcting for the I/Q origin offset.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+-----------------------------------------------------------------------+
    | Name (Value) | Description                                                           |
    +==============+=======================================================================+
    | False (0)    | Disables the I/Q origin offset correction for EDR and LE-HDT packets. |
    +--------------+-----------------------------------------------------------------------+
    | True (1)     | Enables the I/Q origin offset correction for EDR and LE-HDT packets.  |
    +--------------+-----------------------------------------------------------------------+
    """

    MODACC_IQ_MISMATCH_CORRECTION_ENABLED = 11550781
    r"""Specifies whether to enable the IQ mismatch correction for LE- HDT packet. If you set this attribute to **True**, the
    EVM results are computed after correcting for the IQ gain imbalance and quadrature error .
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+---------------------------------------------------------+
    | Name (Value) | Description                                             |
    +==============+=========================================================+
    | False (0)    | Disables the IQ mismatch correction for LE-HDT packets. |
    +--------------+---------------------------------------------------------+
    | True (1)     | Enables the IQ mismatch correction for LE-HDT packets.  |
    +--------------+---------------------------------------------------------+
    """

    MODACC_FREQUENCY_TRACKING_ENABLED = 11550784
    r"""Specifies whether to enable frequency tracking for LE- HDT packet. If you set this attribute to **True**, the Control
    Header EVM, Payload EVM, Payload Frequency Error w1 and Frequency Error w0+w1 results are computed after frequency
    tracking.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+-----------------------------------------------------+
    | Name (Value) | Description                                         |
    +==============+=====================================================+
    | False (0)    | Disables the frequency tracking for LE-HDT packets. |
    +--------------+-----------------------------------------------------+
    | True (1)     | Enables the frequency tracking for LE-HDT packets.  |
    +--------------+-----------------------------------------------------+
    """

    MODACC_AVERAGING_ENABLED = 11550724
    r"""Specifies whether to enable averaging for the ModAcc measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the ModAcc Averaging Count attribute as the number of acquisitions over which the ModAcc            |
    |              | measurement is averaged.                                                                                                 |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODACC_AVERAGING_COUNT = 11550725
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    MODACC_ALL_TRACES_ENABLED = 11550726
    r"""Specifies whether to enable all the traces computed by ModAcc measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    MODACC_NUMBER_OF_ANALYSIS_THREADS = 11550727
    r"""Specifies the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
    range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
    number of threads used depends on the problem size, system resources, data availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    MODACC_RESULTS_DF1AVG_MEAN = 11550729
    r"""Returns the df1avg value computed on the signal.  When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the df1avg results computed for each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_DF1AVG_MAXIMUM = 11550730
    r"""Returns the df1avg value computed on the signal. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
    maximum of the df1avg results computed for each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_DF1AVG_MINIMUM = 11550731
    r"""Returns the df1avg value computed on the signal. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
    minimum of the df1avg results computed for each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_PEAK_DF1MAX_MAXIMUM = 11550732
    r"""Returns the peak df1max value computed on the signal. The measurement computes df1max deviation values on a packet and
    reports the peak value. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
    attribute to **True**, it returns the maximum of the peak df1max results computed for each averaging count. This value
    is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_MINIMUM_DF1MAX_MINIMUM = 11550733
    r"""Returns the minimum df1max value computed on the signal. The measurement computes df1max deviation values on a packet
    and reports the minimum value. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
    minimum of the Min df1max results computed for each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_PERCENTAGE_OF_SYMBOLS_ABOVE_DF1MAX_THRESHOLD = 11550764
    r"""Returns the percentage of symbols with df1max values that are greater than the df1max threshold defined by the
    standard. This result is valid only for the LE packet with a data rate of 125 Kbps. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it computes this
    result using the df1max values from all averaging counts. This value expressed as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_DF2AVG_MEAN = 11550734
    r"""Returns the df2avg value computed on the signal. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the df2avg results computed for each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_DF2AVG_MAXIMUM = 11550735
    r"""Returns the df2avg value computed on the signal. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
    maximum of the df2avg results computed for each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_DF2AVG_MINIMUM = 11550736
    r"""Returns the df2avg value computed on the signal. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
    minimum of the df2avg results computed for each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_PEAK_DF2MAX_MAXIMUM = 11550737
    r"""Returns the peak df2max value computed on the signal. The measurement computes df2max deviation values on a packet and
    reports the peak value. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
    attribute to **True**, it returns the maximum of the peak df2max results computed for each averaging count. This value
    is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_MINIMUM_DF2MAX_MINIMUM = 11550738
    r"""Returns the minimum df2max value computed on the signal. The measurement computes df2max deviation values on a packet
    and reports the minimum value. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
    minimum of the Min df2max results computed for each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_PERCENTAGE_OF_SYMBOLS_ABOVE_DF2MAX_THRESHOLD = 11550739
    r"""Returns the percentage of symbols with df2max values that are greater than the df2max threshold defined by the
    standard. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
    **True**, it computes this result using the df2max values from all averaging counts. This value is expressed as a
    percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_DF3AVG_MEAN = 11550772
    r"""Returns the df3avg value computed on the signal. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the df3avg results computed for each averaging count. This value is expressed in Hz. This result is valid only for
    LE-CS packet with data rate 2 Mbps and when bandwidth bit period product is set to 2.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_PERCENTAGE_OF_SYMBOLS_ABOVE_DF4AVG_THRESHOLD = 11550773
    r"""Returns the percentage of symbols with df4avg values that are greater than the df4avg threshold defined by the
    standard. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
    **True**, it computes this result using the df4avg values from all averaging counts. This value is expressed as a
    percentage. This result is valid only for LE-CS packet with data rate 2 Mbps and when bandwidth bit period product is
    set to 2.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `df1 and df2
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.
    """

    MODACC_RESULTS_BR_INITIAL_FREQUENCY_ERROR_MAXIMUM = 11550740
    r"""Returns the initial frequency error value computed on the preamble portion of the BR packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of the absolute initial frequency error values computed for each averaging count. This
    value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_BR_PEAK_FREQUENCY_DRIFT_MAXIMUM = 11550741
    r"""Returns the peak frequency drift value computed on the BR packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of the absolute peak frequency drift values computed for each averaging count. This value
    is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_BR_PEAK_FREQUENCY_DRIFT_RATE_MAXIMUM = 11550742
    r"""Returns the peak frequency drift rate value computed on the BR packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of the absolute peak frequency drift rate values computed for each averaging count. This
    value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_EDR_HEADER_FREQUENCY_ERROR_WI_MAXIMUM = 11550743
    r"""Returns the frequency error value computed on the header of the EDR packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of the absolute header frequency error values computed for each averaging count. This
    value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_EDR_PEAK_FREQUENCY_ERROR_WI_PLUS_W0_MAXIMUM = 11550744
    r"""Returns the peak frequency error value computed on the EDR portion of the EDR packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of the absolute peak frequency error values computed for each averaging count. This value
    is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_EDR_PEAK_FREQUENCY_ERROR_W0_MAXIMUM = 11550745
    r"""Returns the peak frequency error value computed on the EDR portion of the EDR packet, relative to the header frequency
    error. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
    **True**, it returns the value corresponding to the maximum absolute of the peak frequency error values computed for
    each averaging count. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_LE_INITIAL_FREQUENCY_ERROR_MAXIMUM = 11550769
    r"""Returns the initial frequency error value computed on the preamble portion of the LE or LE-CS packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
    corresponding to the maximum of the absolute initial frequency error values computed for each averaging count. This
    value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_LE_PEAK_FREQUENCY_ERROR_MAXIMUM = 11550746
    r"""When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Disabled**,
    it returns the peak frequency error value computed on the preamble and payload portion of the LE or LE-CS packet. When
    you set the Direction Finding Mode attribute to **Angle of Arrival**, it returns the peak frequency error value
    computed on the Constant tone extension field of the LE packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of absolute the peak frequency error values computed for each averaging count. This value
    is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_LE_INITIAL_FREQUENCY_DRIFT_MAXIMUM = 11550747
    r"""Returns the initial frequency drift value computed on the LE packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of the absolute initial frequency drift values computed for each averaging count. This
    value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_LE_PEAK_FREQUENCY_DRIFT_MAXIMUM = 11550748
    r"""Returns the peak frequency drift value computed on the LE packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of the absolute peak frequency drift values computed for each averaging count. This value
    is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_LE_PEAK_FREQUENCY_DRIFT_RATE_MAXIMUM = 11550749
    r"""Returns the peak frequency drift rate value computed on the LE packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
    corresponding to the maximum of the absolute peak frequency drift rate values computed for each averaging count. This
    value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_PREAMBLE_FREQUENCY_ERROR_W0_MAXIMUM = 11550778
    r"""Returns the frequency error value computed on the preamble portion of the LE-HDT packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
    corresponding to the maximum of the absolute preamble frequency error values computed for each averaging count. This
    value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_PAYLOAD_FREQUENCY_ERROR_W1_MAXIMUM = 11550779
    r"""Returns the frequency error value computed on the payload portion of the LE-HDT packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
    corresponding to the maximum of the absolute payload frequency error values computed for each averaging count. This
    value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_FREQUENCY_ERROR_W0_PLUS_W1_MAXIMUM = 11550780
    r"""Returns the total frequency error  for the LE-HDT packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
    corresponding to the maximum of the absolute frequency error values computed for each averaging count. This value is
    expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the `Frequency Error Measurement
    <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
    concept topic for more details.
    """

    MODACC_RESULTS_PEAK_RMS_DEVM_MAXIMUM = 11550750
    r"""Returns the peak of the RMS differential EVM (DEVM) values computed on each 50us block of the EDR portion of the EDR
    packet. When you set :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**,
    it returns the maximum of the peak RMS differential EVM (DEVM) values computed for each averaging count. This value is
    expressed as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the EDR Differential EVM concept topic for more details.
    """

    MODACC_RESULTS_RMS_DEVM_MEAN = 11550751
    r"""Returns the RMS differential EVM (DEVM) value computed on the EDR portion of the EDR packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the RMS differential EVM (DEVM) values computed for each averaging count. This value is expressed as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    Refer to the EDR Differential EVM concept topic for more details.
    """

    MODACC_RESULTS_PEAK_DEVM_MAXIMUM = 11550752
    r"""Returns the peak of the differential EVM (DEVM) values computed on symbols in the EDR portion of the EDR packet. When
    you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
    returns the maximum of the peak symbol differential EVM (DEVM) values computed for each averaging count. This value is
    expressed as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_99_PERCENT_DEVM = 11550753
    r"""Returns the 99th percentile of the differential EVM (DEVM) values computed on symbols of the EDR portion of all
    measured EDR packets. This value is expressed as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_PERCENTAGE_OF_SYMBOLS_BELOW_99_PERCENT_DEVM_LIMIT = 11550754
    r"""Returns the percentage of symbols in the EDR portion of all the measured EDR packets with differential EVM (DEVM) less
    than or equal to 99% DEVM threshold as defined in section 4.5.11 of the *Bluetooth Test Specification RF.TS.p33.*. When
    you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
    computes this result using the symbol DEVM values from all averaging counts. This value is expressed as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_AVERAGE_RMS_MAGNITUDE_ERROR_MEAN = 11550765
    r"""Returns the average of the RMS magnitude error values computed on each 50 us block of EDR portion of the EDR packet.
    When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
    returns the mean of the average RMS magnitude error values computed for each averaging count. This value is expressed
    as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_PEAK_RMS_MAGNITUDE_ERROR_MAXIMUM = 11550766
    r"""Returns the peak of the RMS magnitude error values computed on each 50 us block of EDR portion of the EDR packet. When
    you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**,  it
    returns the maximum of the peak RMS Magnitude error values computed for each averaging count. This value is expressed
    as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_AVERAGE_RMS_PHASE_ERROR_MEAN = 11550767
    r"""Return the average of the RMS phase error values computed on each 50 us block of EDR portion of the EDR packet. When
    you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
    returns the mean of the average RMS phase error values computed for each averaging count. This value is expressed in
    degrees.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_PEAK_RMS_PHASE_ERROR_MAXIMUM = 11550768
    r"""Return the peak of the RMS phase error values computed on each 50 us block of EDR portion of the EDR packet. When you
    set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns
    the maximum of the peak RMS phase error values computed for each averaging count. This value is expressed in degrees.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_PREAMBLE_RMS_EVM_MEAN = 11550774
    r"""Returns the RMS EVM value computed on the preamble portion of the LE-HDT packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid only for
    LE-HDT packet.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_CONTROL_HEADER_RMS_EVM_MEAN = 11550775
    r"""Returns the RMS EVM value computed on the control header portion of the LE-HDT packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid only for
    LE-HDT packet.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_PAYLOAD_RMS_EVM_MEAN = 11550776
    r"""Returns the RMS EVM value computed on the payload portion including the payload header of the LE-HDT packet. When you
    set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns
    the mean of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid
    only for LE-HDT packet.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_IQ_ORIGIN_OFFSET_MEAN = 11550755
    r"""Returns the I/Q origin offset estimated over the EDR portion of the EDR packets and preamble portion of the LE-HDT
    packets. This value is expressed in dB. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the I/Q origin offset values computed for each averaging count.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_IQ_GAIN_IMBALANCE_MEAN = 11550782
    r"""Returns the IQ gain imbalance estimated over preamble portion of the LE-HDT packets. This value is expressed in dB.
    When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
    returns the mean of the IQ gain imbalance values computed for each averaging count.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_QUADRATURE_ERROR_MEAN = 11550783
    r"""Returns the quadrature error estimated over preamble portion of the LE-HDT packets. This value is expressed in degree.
    When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
    returns the mean of the quadrature error values computed for each averaging count.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_CLOCK_DRIFT_MEAN = 11550770
    r"""Returns the clock drift estimated over the LE-CS packet. This value is expressed in ppm. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the clock drift values computed for each averaging count.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_PREAMBLE_START_TIME_MEAN = 11550771
    r"""Returns the start time of the preamble of LE-CS packet. This value is expressed in seconds. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
    of the preamble start time values computed for each averaging count.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODACC_RESULTS_FRACTIONAL_TIME_OFFSET_MEAN = 11550777
    r"""Returns the fractional time offset value computed on the sounding sequence portion of the LE CS Packet. This value is
    expressed in seconds. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
    attribute to **True**, it returns the mean of the fractional time offset values for each averaging count.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    ACP_MEASUREMENT_ENABLED = 11554816
    r"""Specifies whether to enable the ACP measurement.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is FALSE.
    """

    ACP_OFFSET_CHANNEL_MODE = 11554818
    r"""Specifies which offset channels are used for the measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Symmetric**.
    
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)  | Description                                                                                                              |
    +===============+==========================================================================================================================+
    | Symmetric (0) | Specifies that the offset channels are symmetrically located around the reference channel. The number of offsets on      |
    |               | either side of the reference channel is specified by the ACP Num Offsets attribute. In symmetric mode, the               |
    |               | Center Frequency attribute specifies the frequency of the reference channel, expressed in Hz.                            |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | In-band (1)   | Specifies that the measurement is performed over all the channels as specified by the standard. For BR and EDR packets,  |
    |               | 79 channels starting from 2.402GHz to 2.48GHz are used for the measurement. For LE packets, 81 channels starting from    |
    |               | 2.401GHz to 2.481GHz are used for the measurement. In In-band mode, the Center Frequency attribute specifies the         |
    |               | frequency of acquisition which must be equal to 2.441GHz. Configure the Channel Number attribute to specify the          |
    |               | frequency of the reference channel.                                                                                      |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_NUMBER_OF_OFFSETS = 11554819
    r"""Specifies the number of offset channels used on either side of the reference channel for the adjacent channel power
    (ACP) measurement when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute
    to **Symmetric**. This attribute also returns the actual number of offsets used in the ACP measurement when you set the
    ACP Offset Channel Mode attribute to **In-band**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 5. Valid values are 0 to 100, inclusive.
    """

    ACP_OFFSET_FREQUENCY = 11554820
    r"""Returns the frequency of the offset channel with respect to the reference channel frequency. This value is expressed in
    Hz.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1 MHz.
    """

    ACP_REFERENCE_CHANNEL_BANDWIDTH_MODE = 11554838
    r"""+--------------+-------------+
    | Name (Value) | Description |
    +==============+=============+
    | Auto (0)     |             |
    +--------------+-------------+
    | Manual (1)   |             |
    +--------------+-------------+
    """

    ACP_REFERENCE_CHANNEL_BANDWIDTH = 11554837
    r"""
    """

    ACP_BURST_SYNCHRONIZATION_TYPE = 11554834
    r"""Specifies the type of synchronization used for detecting the start of the EDR packet in the adjacent channel power
    (ACP) measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Preamble**.
    
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)  | Description                                                                                                              |
    +===============+==========================================================================================================================+
    | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.                       |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Preamble (1)  | Specifies that the measurement uses the preamble field bits to detect the start of the packet.                           |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Sync Word (2) | Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to      |
    |               | detect the start of the packet. For BR /EDR packets, the sync word is derived from the BD Address LAP attribute.         |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_AVERAGING_ENABLED = 11554821
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
    | True (1)     | The measurement uses the ACP Averaging Count attribute as the number of acquisitions over which the ACP measurement is   |
    |              | averaged.                                                                                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_AVERAGING_COUNT = 11554822
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    ACP_ALL_TRACES_ENABLED = 11554823
    r"""Specifies whether to enable all traces for the adjacent channel power (ACP) measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    ACP_NUMBER_OF_ANALYSIS_THREADS = 11554824
    r"""Specifies the maximum number of threads used for parallelism for adjacent channel power (ACP) measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    ACP_RESULTS_MEASUREMENT_STATUS = 11554826
    r"""Indicates the overall measurement status based on the measurement limits specified by the standard when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**.
    
    The standard defines two masks, mask with exception and mask without exception. Mask with exception is more
    stringent than mask without exception.
    
    The mask with exception limits are as follows:
    
    +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
    | PHY | Data Rate (bps) | Offset 0                                                   | Offset 1                      | Offset 2                      | Offset 3                      | Offset 4                      | Offset (greater than or equal to 5) |
    +=====+=================+============================================================+===============================+===============================+===============================+===============================+=====================================+
    | BR  | NA              | NA                                                         | less than or equal to -20 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm       |
    +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
    | EDR | NA              | less than or equal to (Reference Channel Power (dBm) - 26) | less than or equal to -20 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm       |
    +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
    | LE  | 1 Mbps          | NA                                                         | less than or equal to -20 dBm | less than or equal to -30 dBm | less than or equal to -30 dBm | less than or equal to -30 dBm | less than or equal to -30 dBm       |
    +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
    | LE  | 2 Mbps          | NA                                                         | NA                            | NA                            | less than or equal to -20 dBm | less than or equal to -20 dBm | less than or equal to -30 dBm       |
    +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
    
    The mask without exception limits for all packet type are as follows:
    
    +-----+-----------------+-------------------------------+-------------------------------------+
    | PHY | Data Rate (bps) | Offset (2) to Offset (4)      | Offset (greater than or equal to 5) |
    +=====+=================+===============================+=====================================+
    | BR  | NA              | less than or equal to -20 dBm | less than or equal to -20 dBm       |
    +-----+-----------------+-------------------------------+-------------------------------------+
    | EDR | NA              | less than or equal to -20 dBm | less than or equal to -20 dBm       |
    +-----+-----------------+-------------------------------+-------------------------------------+
    | LE  | 1 Mbps          | less than or equal to -20 dBm | less than or equal to -20 dBm       |
    +-----+-----------------+-------------------------------+-------------------------------------+
    | LE  | 2 Mbps          | NA                            | less than or equal to -20 dBm       |
    +-----+-----------------+-------------------------------+-------------------------------------+
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    
    +---------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)        | Description                                                                                                              |
    +=====================+==========================================================================================================================+
    | Not Applicable (-1) | This attribute returns Not Applicable when you set the ACP Offset Channel Mode attribute to Symmetric.                   |
    +---------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Fail (0)            | This attribute returns Fail if more than 3 offsets from offset 3 onwards fail the mask with exception or any offset      |
    |                     | channel fails the mask without exception.                                                                                |
    +---------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Pass (1)            | This attribute returns Pass if all offsets except up to a maximum of 3 from offset 3 onwards do not fail the mask with   |
    |                     | exception and all offset channels do not fail the mask without exception.                                                |
    +---------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    ACP_RESULTS_REFERENCE_CHANNEL_POWER = 11554827
    r"""Returns the measured power of the reference channel. This value is expressed in dBm.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    ACP_RESULTS_LOWER_OFFSET_ABSOLUTE_POWER = 11554828
    r"""Returns the absolute power measured in the lower offset channel. This value is expressed in dBm.
    
    Use "offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_LOWER_OFFSET_RELATIVE_POWER = 11554829
    r"""Returns the relative power in the lower offset channel measured with respect to the reference channel power. This value
    is expressed in dB.
    
    Use "offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_LOWER_OFFSET_MARGIN = 11554830
    r"""Returns the margin from the limit specified by the mask with exception for lower offsets. This value is expressed in
    dB. Margin is defined as the difference between the offset absolute power and mask with exception. This result is valid
    only if you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to
    **In-band**. This attribute returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.
    
    Use "offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_UPPER_OFFSET_ABSOLUTE_POWER = 11554831
    r"""Returns the absolute power measured in the upper offset channel. This value is expressed in dBm.
    
    Use "offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_UPPER_OFFSET_RELATIVE_POWER = 11554832
    r"""Returns the relative power in the upper offset channel measured with respect to the reference channel power. This value
    is expressed in dB.
    
    Use "offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_UPPER_OFFSET_MARGIN = 11554833
    r"""Returns the margin from the limit specified by the mask with exception for upper offsets. This value is expressed in
    dB. Margin is defined as the difference between the offset absolute power and mask with exception. This result is valid
    only if you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to
    **In-band**. This attribute returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.
    
    Use "offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    TWENTY_DB_BANDWIDTH_MEASUREMENT_ENABLED = 11542528
    r"""Specifies whether to enable the 20dBBandwidth measurement specified in section 4.5.5 of the *Bluetooth Test
    Specification RF.TS.p33*. The measurement uses a span of 3 MHz internally. This measurement is valid only for basic
    rate (BR) packets.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    TWENTY_DB_BANDWIDTH_AVERAGING_ENABLED = 11542530
    r"""Specifies whether to enable averaging for the 20dBBandwidth measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The 20dBBandwidth measurement uses the 20dBBandwidth Averaging Count attribute as the number of acquisitions over which  |
    |              | the 20dBBandwidth measurement is averaged.                                                                               |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    TWENTY_DB_BANDWIDTH_AVERAGING_COUNT = 11542531
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    TWENTY_DB_BANDWIDTH_ALL_TRACES_ENABLED = 11542532
    r"""Specifies whether to enable all the traces for the 20dBBandwidth measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    TWENTY_DB_BANDWIDTH_NUMBER_OF_ANALYSIS_THREADS = 11542533
    r"""Specifies the maximum number of threads used for parallelism for the 20dB bandwidth measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    TWENTY_DB_BANDWIDTH_RESULTS_PEAK_POWER = 11542535
    r"""Returns the peak power of the measured spectrum. This value is expressed in dBm.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TWENTY_DB_BANDWIDTH_RESULTS_BANDWIDTH = 11542536
    r"""Returns the 20dB bandwidth of the received signal. It is computed as the difference between 20dBBandwidth Results High
    Freq and 20dBBandwidth Results Low Freq. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TWENTY_DB_BANDWIDTH_RESULTS_HIGH_FREQUENCY = 11542537
    r"""Returns the highest frequency above the center frequency at which the transmit power drops 20 dB below the peak power.
    This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TWENTY_DB_BANDWIDTH_RESULTS_LOW_FREQUENCY = 11542538
    r"""Returns the lowest frequency below the center frequency at which the transmit power drops 20 dB below the peak power.
    This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    FREQUENCY_RANGE_MEASUREMENT_ENABLED = 11546624
    r"""Specifies whether to enable the FrequencyRange measurement specified in the section 4.5.4 of the *Bluetooth Test
    Specification RF.TS.p33*. This measurement is valid only for basic rate (BR) packets.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    FREQUENCY_RANGE_SPAN = 11546626
    r"""Specifies the span for the FrequencyRange measurement. This value is expressed in Hz. You must adjust the span
    according the center frequency as specified in section 4.5.4 of the *Bluetooth Test Specification RF.TS.p33*. It is
    recommended to use the span of 6 MHz for a center frequency of 2.402 GHz and 10 MHz for a center frequency of 2.48 GHz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10 MHz.
    """

    FREQUENCY_RANGE_AVERAGING_ENABLED = 11546627
    r"""Specifies whether to enable averaging for the FrequencyRange measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The FrequencyRange measurement uses the FrequencyRange Averaging Count attribute as the number of acquisitions over      |
    |              | which the FrequencyRange measurement is averaged.                                                                        |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    FREQUENCY_RANGE_AVERAGING_COUNT = 11546628
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.FREQUENCY_RANGE_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    FREQUENCY_RANGE_ALL_TRACES_ENABLED = 11546629
    r"""Specifies whether to enable all the traces for FrequencyRange measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    FREQUENCY_RANGE_NUMBER_OF_ANALYSIS_THREADS = 11546630
    r"""Specifies the maximum number of threads used for parallelism for the frequency range measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    FREQUENCY_RANGE_RESULTS_HIGH_FREQUENCY = 11546632
    r"""Returns the highest frequency above the center frequency at which the transmit power drops below -30 dBm measured in a
    100 kHz bandwidth. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    FREQUENCY_RANGE_RESULTS_LOW_FREQUENCY = 11546633
    r"""Returns the lowest frequency below the center frequency at which the transmit power drops below -30 dBm measured in a
    100 kHz bandwidth. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODSPECTRUM_MEASUREMENT_ENABLED = 11595776
    r"""Specifies whether to enable the ModSpectrum measurements.This measurement is valid only for channel sounding (CS)
    packets.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    MODSPECTRUM_BURST_SYNCHRONIZATION_TYPE = 11595778
    r"""Specifies the type of synchronization used for detecting the start of packet in the ModSpectrum measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Preamble**.
    
    +---------------+-------------------------------------------------------------------------------------------------------------+
    | Name (Value)  | Description                                                                                                 |
    +===============+=============================================================================================================+
    | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.          |
    +---------------+-------------------------------------------------------------------------------------------------------------+
    | Preamble (1)  | Specifies that the measurement uses the preamble field to detect the start of the packet.                   |
    +---------------+-------------------------------------------------------------------------------------------------------------+
    | Sync Word (2) | Specifies that the measurement uses the Access Address for LE-CS packets to detect the start of the packet. |
    +---------------+-------------------------------------------------------------------------------------------------------------+
    """

    MODSPECTRUM_AVERAGING_ENABLED = 11595779
    r"""Specifies whether to enable averaging for ModSpectrum measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the ModSpectrum Averaging Count attribute as the number of acquisitions over which the ModSpectrum  |
    |              | measurement is averaged.                                                                                                 |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    MODSPECTRUM_AVERAGING_COUNT = 11595780
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODSPECTRUM_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    MODSPECTRUM_ALL_TRACES_ENABLED = 11595781
    r"""Specifies whether to enable all the traces used for ModSpectrum measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    MODSPECTRUM_NUMBER_OF_ANALYSIS_THREADS = 11595782
    r"""Specifies the maximum number of threads used for parallelism for ModSpectrum measurement.
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    MODSPECTRUM_RESULTS_BANDWIDTH = 11595784
    r"""Returns the 6 dB bandwidth of the received signal. It is computed as the difference between
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODSPECTRUM_RESULTS_HIGH_FREQUENCY`  and
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODSPECTRUM_RESULTS_LOW_FREQUENCY` . This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODSPECTRUM_RESULTS_HIGH_FREQUENCY = 11595785
    r"""Returns the highest frequency above the center frequency at which the transmit power drops 6dB below the peak power.
    This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    MODSPECTRUM_RESULTS_LOW_FREQUENCY = 11595786
    r"""Returns the lowest frequency below the center frequency at which the transmit power drops 6 dB below the peak power.
    This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_MEASUREMENT_ENABLED = 11538432
    r"""Specifies whether to enable the transmit power (TxP) measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    TXP_BURST_SYNCHRONIZATION_TYPE = 11538448
    r"""Specifies the type of synchronization used for detecting the start of packet in the transmit power (TXP) measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Preamble**.
    
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)  | Description                                                                                                              |
    +===============+==========================================================================================================================+
    | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.                       |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Preamble (1)  | Specifies that the measurement uses the preamble field to detect the start of the packet.                                |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    | Sync Word (2) | Specifies that the measurement uses sync word for the BR/EDR packets and access address for LE/LE-CS packets to detect   |
    |               | the start of the packet. For BR /EDR packets, the sync word is derived from the BD Address LAP attribute.                |
    +---------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    TXP_AVERAGING_ENABLED = 11538434
    r"""Specifies whether to enable averaging for the transmit power (TxP) measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the TXP Averaging Count attribute as the number of acquisitions over which the TXP measurement is   |
    |              | averaged.                                                                                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    TXP_AVERAGING_COUNT = 11538435
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    TXP_ALL_TRACES_ENABLED = 11538436
    r"""Specifies whether to enable all the traces used for transmit power (TxP) measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    TXP_NUMBER_OF_ANALYSIS_THREADS = 11538437
    r"""Specifies the maximum number of threads used for parallelism for TXP measurement.
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    TXP_RESULTS_AVERAGE_POWER_MEAN = 11538439
    r"""Returns the average power computed over the measurement interval. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
    packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
    average power is calculated from beginning of the payload portion. This value is expressed in dBm. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
    the average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_AVERAGE_POWER_MAXIMUM = 11538440
    r"""Returns the average power computed over the measurement interval. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
    packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
    average power is calculated from beginning of the payload portion. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
    of the average power results computed for each averaging count. This value is expressed in dBm.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_AVERAGE_POWER_MINIMUM = 11538441
    r"""Returns the average power computed over the measurement interval. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
    packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
    average power is calculated from beginning of the payload portion. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the minimum
    of the average power results computed for each averaging count. This value is expressed in dBm.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_PEAK_POWER_MAXIMUM = 11538442
    r"""Returns the peak power computed over the measurement interval. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
    packets, it will exclude guard period and all the switching slots for the peak power computation. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
    of the peak power results computed for each averaging count. This value is expressed in dBm.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_PEAK_TO_AVERAGE_POWER_RATIO_MAXIMUM = 11538443
    r"""Returns the peak to average power ratio computed over the measurement interval. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
    packets, it will exclude guard period and all the switching slots for the peak to average power ratio computation. For
    LE-HDT, PAPR is calculated using peak power calculated over active portion of burst and average power calculated from
    beginning of the payload portion. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
    of the peak to average power ratio results computed for each averaging count. This value is expressed in dB.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_EDR_GFSK_AVERAGE_POWER_MEAN = 11538444
    r"""Returns the average power of the GFSK portion of the EDR packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
    the GFSK average power results computed for each averaging count. This value is expressed in dBm.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_EDR_DPSK_AVERAGE_POWER_MEAN = 11538445
    r"""Returns the average power of the DPSK portion of the EDR packet. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
    the DPSK average power results computed for each averaging count. This value is expressed in dBm.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_EDR_DPSK_GFSK_AVERAGE_POWER_RATIO_MEAN = 11538451
    r"""Returns the ratio of the average power of the DPSK portion to the average power of the GFSK portion of the EDR packet.
    When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
    returns the mean of the DPSK GFSK average power ratio results computed for each averaging count. This value is
    expressed in dB.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_LE_CTE_REFERENCE_PERIOD_AVERAGE_POWER_MEAN = 11538452
    r"""Returns the average power computed over the reference period in the CTE portion of the LE packet. This result is
    applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to
    **Angle of Departure**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED`
    attribute to **True**, it returns the mean of the CTE reference period average power results computed for each
    averaging count. This value is expressed in dBm.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_LE_CTE_REFERENCE_PERIOD_PEAK_ABSOLUTE_POWER_DEVIATION_MAXIMUM = 11538453
    r"""Returns the peak absolute power deviation computed over the reference period in the CTE portion of the LE packet. The
    peak absolute power deviation is the  deviation of peak power with respect to the average power in the reference
    period. This result is applicable only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**. When you
    set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the
    maximum of the CTE reference period absolute power deviation results computed for each averaging count. This value is
    expressed as a percentage.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals and results.
    """

    TXP_RESULTS_LE_CTE_TRANSMIT_SLOT_AVERAGE_POWER_MEAN = 11538454
    r"""Returns the average power computed over each transmit slot in CTE portion of the LE packet. This result is applicable
    only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of
    Departure**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to
    **True**, it returns the mean of the CTE transmit slot average power results computed for each averaging count. This
    value is expressed in dBm.
    
    Use "slot<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    TXP_RESULTS_LE_CTE_TRANSMIT_SLOT_PEAK_ABSOLUTE_POWER_DEVIATION_MAXIMUM = 11538455
    r"""Returns the peak absolute power deviation computed over each transmit slot in the CTE portion of the LE packet. The
    peak absolute power deviation is the deviation of peak power in each transmit slot with respect to the average power in
    that transmit slot. This result is applicable only when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**. When you
    set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the
    maximum of the CTE transmit slot absolute power deviation results computed for each averaging count. This value is
    expressed as a percentage.
    
    Use "slot<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    TXP_RESULTS_LE_CS_PHASE_MEASUREMENT_PERIOD_AVERAGE_POWER_MEAN = 11538456
    r"""Returns the average power computed over each antenna path during phase measurement period of the LE-CS packet. This
    result is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to
    **LE-CS** and the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any
    value other than **SYNC**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED`
    attribute to **True**, it returns the mean of the phase measurement period average power results computed for each
    averaging count. This value is expressed in dBm.
    
    Use "slot<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    POWERRAMP_MEASUREMENT_ENABLED = 11591680
    r"""Specifies whether to enable PowerRamp  measurements.
    This measurement is valid only for low energy CS (LE-CS) packets.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    POWERRAMP_BURST_SYNCHRONIZATION_TYPE = 11591682
    r"""Specifies the type of synchronization used for detecting the start of packet in the PowerRamp measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Preamble**.
    
    +---------------+-------------------------------------------------------------------------------------------------------------+
    | Name (Value)  | Description                                                                                                 |
    +===============+=============================================================================================================+
    | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.          |
    +---------------+-------------------------------------------------------------------------------------------------------------+
    | Preamble (1)  | Specifies that the measurement uses the preamble field bits to detect the start of the packet.              |
    +---------------+-------------------------------------------------------------------------------------------------------------+
    | Sync Word (2) | Specifies that the measurement uses the Access Address for LE-CS packets to detect the start of the packet. |
    +---------------+-------------------------------------------------------------------------------------------------------------+
    """

    POWERRAMP_AVERAGING_ENABLED = 11591685
    r"""Specifies whether to enable averaging for PowerRamp measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the PowerRamp Averaging Count attribute as the number of acquisitions over which the PowerRamp      |
    |              | measurement is averaged.                                                                                                 |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    POWERRAMP_AVERAGING_COUNT = 11591686
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    POWERRAMP_NUMBER_OF_ANALYSIS_THREADS = 11591687
    r"""Specifies the maximum number of threads used for parallelism for PowerRamp measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    POWERRAMP_RESULTS_RISE_TIME_MEAN = 11591689
    r"""Rise Time returns the rise time of the acquired signal that is the amount of time taken for the power envelope to rise
    from a level of 10 percent to 90 percent. When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**, this parameter
    returns the mean of the rise time computed for each averaging count. This value is expressed in seconds.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    POWERRAMP_RESULTS_FALL_TIME_MEAN = 11591690
    r"""Fall Time returns the fall time of the acquired signal that is the amount of time taken for the power envelope to fall
    from a level of 90 percent to 10 percent.  When you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**,this parameter
    returns the mean of the fall time computed for each averaging countt. This value is expressed in seconds.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    POWERRAMP_RESULTS_40DB_FALL_TIME_MEAN = 11591691
    r"""40dB Fall Time returns the fall time of the acquired signal at which transmit power drops 40 dB below average power.
    When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**,
    this parameter returns the mean of the 40dB fall time computed for each averaging count. This value is expressed in
    seconds.
    
    You do not need to use a selector string to read this result for the default signal and result instance. Refer
    to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    LIMITED_CONFIGURATION_CHANGE = 11587584
    r"""Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.
    
    If your test system performs the same measurement at different selected ports, multiple frequencies and/or
    power levels repeatedly, enabling this attribute can help achieve faster measurements. When you set this attribute to a
    value other than Disabled, the RFmx driver will use an optimized code path and skip some checks. Because RFmx skips
    some checks when you use this attribute, you need to be aware of the limitations of this feature, which are listed in
    the `Limitations of the Limited Configuration Change Property
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
    Selector String topic for information about the string syntax for named signals.
    
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

    AUTO_LEVEL_INITIAL_REFERENCE_LEVEL = 11587585
    r"""Specifies the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
    input signal. This value is expressed in dBm.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 30.
    """

    RESULT_FETCH_TIMEOUT = 11583488
    r"""Specifies the time, in seconds, to wait before results are available in the RFmxBluetooth Attribute. Set this value to a time
    longer than expected for fetching the measurement. A value of -1 specifies that the RFmxBluetooth Attribute waits until the
    measurement is complete.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """
