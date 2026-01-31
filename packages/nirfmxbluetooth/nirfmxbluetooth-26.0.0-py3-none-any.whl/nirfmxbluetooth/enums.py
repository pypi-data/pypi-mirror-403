"""enums.py - Contains enum classes."""

from enum import Enum, IntFlag


class TriggerType(Enum):
    """TriggerType."""

    NONE = 0
    r"""No reference trigger is used for signal acquisition."""

    DIGITAL_EDGE = 1
    r"""A digital-edge trigger is used for signal acquisition. The source of the digital edge is specified using the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE` attribute."""

    IQ_POWER_EDGE = 2
    r"""An I/Q power-edge trigger is used for signal acquisition, which is configured using the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute."""

    SOFTWARE = 3
    r"""A software trigger is used for signal acquisition."""


class DigitalEdgeTriggerEdge(Enum):
    """DigitalEdgeTriggerEdge."""

    RISING = 0
    r"""The trigger asserts on the rising edge of the signal."""

    FALLING = 1
    r"""The trigger asserts on the falling edge of the signal."""


class IQPowerEdgeTriggerLevelType(Enum):
    """IQPowerEdgeTriggerLevelType."""

    RELATIVE = 0
    r"""The IQ Power Edge Level attribute is relative to the value of the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.REFERENCE_LEVEL` attribute."""

    ABSOLUTE = 1
    r"""The IQ Power Edge Level attribute specifies the absolute power."""


class IQPowerEdgeTriggerSlope(Enum):
    """IQPowerEdgeTriggerSlope."""

    RISING = 0
    r"""The trigger asserts when the signal power is rising."""

    FALLING = 1
    r"""The trigger asserts when the signal power is falling."""


class TriggerMinimumQuietTimeMode(Enum):
    """TriggerMinimumQuietTimeMode."""

    MANUAL = 0
    r"""The minimum quiet time for triggering is the value of the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION` attribute."""

    AUTO = 1
    r"""The measurement computes the minimum quiet time used for triggering."""


class PacketType(Enum):
    """PacketType."""

    UNKNOWN = -1
    r"""Specifies that no valid bluetooth packet is detected in the signal to be measured."""

    PACKET_TYPE_DH1 = 0
    r"""Specifies that the packet type is DH1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.2, Part B,
    Volume 2 of the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_DH3 = 1
    r"""Specifies that the packet type is DH3. The packet belongs to BR PHY. Refer to section 6.5.4.4, Part B, Volume 2 of the
    *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_DH5 = 2
    r"""Specifies that the packet type is DH5. The packet belongs to BR PHY. Refer to section 6.5.4.6, Part B, Volume 2 of the
    *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_DM1 = 3
    r"""Specifies that the packet type is DM1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.1, Part B,
    Volume 2 of the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_DM3 = 4
    r"""Specifies that the packet type is DM3. The packet belongs to BR PHY. Refer to section 6.5.4.3, Part B, Volume 2 of the
    *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_DM5 = 5
    r"""Specifies that the packet type is DM5. The packet belongs to BR PHY. Refer to section 6.5.4.5, Part B, Volume 2 of the
    *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_2_DH1 = 6
    r"""Specifies that the packet type is 2-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.8, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_2_DH3 = 7
    r"""Specifies that the packet type is 2-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.9, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_2_DH5 = 8
    r"""Specifies that the packet type is 2-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.10, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_3_DH1 = 9
    r"""Specifies that the packet type is 3-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.11, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_3_DH3 = 10
    r"""Specifies that the packet type is 3-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.12, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_3_DH5 = 11
    r"""Specifies that the packet type is 3-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.13, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_2_EV3 = 12
    r"""Specifies that the packet type is 2-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.4, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_2_EV5 = 13
    r"""Specifies that the packet type is 2-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.5, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_3_EV3 = 14
    r"""Specifies that the packet type is 3-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.6, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_3_EV5 = 15
    r"""Specifies that the packet type is 3-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.7, Part B, Volume 2 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_LE = 16
    r"""Specifies that the packet type is LE. The packet belongs to LE PHY. Refer to sections 2.1 and 2.2, Part B, Volume 6 of
    the *Bluetooth Core Specification v6.0* for more information about this packet."""

    PACKET_TYPE_LE_CS = 17
    r"""Specifies that the packet type is LE-CS. The packet belongs to LE-CS PHY. Refer to Section 2, Part H, Volume 6 of the
    Bluetooth Specification v6.0 for more information about this packet"""

    PACKET_TYPE_LE_HDT = 18
    r"""Specifies that the packet type is LE-HDT. The packet belongs to LE-HDT PHY."""


class PayloadBitPattern(Enum):
    """PayloadBitPattern."""

    STANDARD_DEFINED = 0
    r"""Specifies that the payload bit pattern is **Standard Defined**."""

    PATTERN_11110000 = 1
    r"""Specifies that the payload bit pattern is **11110000**."""

    PATTERN_10101010 = 2
    r"""Specifies that the payload bit pattern is **10101010**."""


class PayloadLengthMode(Enum):
    """PayloadLengthMode."""

    MANUAL = 0
    r"""Enables the value specified by the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH` attribute. The
    acquisition and measurement durations will be decided based on this value."""

    AUTO = 1
    r"""Enables the standard defined maximum payload length for BR, EDR, LE and LE-CS packet, and the maximum payload zone
    length for LE-HDT packet. If this attribute is set to Auto, the maximum standard defined payload length or payload zone
    length for the selected Packet Type is chosen. The maximum payload length a device under test (DUT) can generate varies
    from 37 to 255 bytes for LE packet, and the maximum payload zone length varies from 514 to 33020 bytes for LE-HDT
    packet. When you set the payload length mode to **Auto**, RFmx chooses 37 bytes for LE packet and 514 bytes for LE-HDT
    packet."""


class DirectionFindingMode(Enum):
    """DirectionFindingMode."""

    DISABLED = 0
    r"""Specifies that the LE packet does not have fields required for direction finding."""

    ANGLE_OF_ARRIVAL = 1
    r"""Specifies that the LE packets uses the Angle of Arrival method of direction finding."""

    ANGLE_OF_DEPARTURE = 2
    r"""Specifies that the LE packets uses the Angle of Departure method of direction finding."""


class ChannelSoundingPacketFormat(Enum):
    """ChannelSoundingPacketFormat."""

    SYNC = 0
    r"""Specifies that the LE-CS packet contains only SYNC portion."""

    CS_TONE = 1
    r"""Specifies that the LE-CS packet contains only CS Tone."""

    CS_TONE_AFTER_SYNC = 2
    r"""Specifies that the CS Tone portion is at the end of the LE-CS packet."""

    CS_TONE_BEFORE_SYNC = 3
    r"""Specifies that the CS Tone portion is at the beginning of the LE-CS packet."""


class ChannelSoundingSyncSequence(Enum):
    """ChannelSoundingSyncSequence."""

    NONE = 0
    r"""Specifies that there is no optional sequence at the end of the SYNC portion of the LE-CS packet."""

    SOUNDING_SEQUENCE_32_BIT = 1
    r"""Specifies that there is a 32-bit sounding sequence at the end of the SYNC portion of the LE-CS packet."""

    SOUNDING_SEQUENCE_96_BIT = 2
    r"""Specifies that there is a 96-bit sounding sequence at the end of the SYNC portion of the LE-CS packet."""

    PAYLOAD_PATTERN = 3
    r"""Specifies that the payload bit pattern is present at the end of the SYNC portion of the LE-CS packet."""


class ChannelSoundingToneExtensionSlot(Enum):
    """ChannelSoundingToneExtensionSlot."""

    DISABLED = 0
    r"""Specifies that there is no transmission in the CS Tone extension slot."""

    ENABLED = 1
    r"""Specifies that there is transmission in the CS Tone extension slot."""


class HighDataThroughputPacketFormat(Enum):
    """HighDataThroughputPacketFormat."""

    SHORT_FORMAT = 0
    r"""Specifies that the HDT packet format is Short Format. This packet consists of preamble and control header field."""

    FORMAT0 = 1
    r"""Specifies that the HDT packet format is Format0. This packet consists of preamble, control header, PDU header and
    payload field. The maximum payload length is 510 bytes."""

    FORMAT1 = 2
    r"""Specifies that the HDT packet format is Format1. This packet format is similar to the Format0 but its payload zone
    consists of multiple blocks and the maximum payload length per payload is 8191 bytes."""


class VhdtModeEnabled(Enum):
    """VhdtModeEnabled."""

    FALSE = 0
    r""""""

    TRUE = 1
    r""""""


class ModAccBurstSynchronizationType(Enum):
    """ModAccBurstSynchronizationType."""

    NONE = 0
    r"""Specifies that the measurement does not perform synchronization to detect the start of the packet."""

    PREAMBLE = 1
    r"""Specifies that the measurement uses the preamble field to detect the start of the packet."""

    SYNC_WORD = 2
    r"""Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to
    detect the start of the packet. For BR /EDR packets, the sync word is derived from the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.BD_ADDRESS_LAP` attribute."""


class ModAccIQOriginOffsetCorrectionEnabled(Enum):
    """ModAccIQOriginOffsetCorrectionEnabled."""

    FALSE = 0
    r"""Disables the I/Q origin offset correction for EDR and LE-HDT packets."""

    TRUE = 1
    r"""Enables the I/Q origin offset correction for EDR and LE-HDT packets."""


class ModAccIQMismatchCorrectionEnabled(Enum):
    """ModAccIQMismatchCorrectionEnabled."""

    FALSE = 0
    r"""Disables the IQ mismatch correction for LE-HDT packets."""

    TRUE = 1
    r"""Enables the IQ mismatch correction for LE-HDT packets."""


class ModAccFrequencyTrackingEnabled(Enum):
    """ModAccFrequencyTrackingEnabled."""

    FALSE = 0
    r"""Disables the frequency tracking for LE-HDT packets."""

    TRUE = 1
    r"""Enables the frequency tracking for LE-HDT packets."""


class ModAccAveragingEnabled(Enum):
    """ModAccAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement uses the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_COUNT` attribute as the
    number of acquisitions over which the ModAcc measurement is averaged."""


class AcpOffsetChannelMode(Enum):
    """AcpOffsetChannelMode."""

    SYMMETRIC = 0
    r"""Specifies that the offset channels are symmetrically located around the reference channel. The number of offsets on
    either side of the reference channel is specified by the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_NUMBER_OF_OFFSETS` attribute. In symmetric mode, the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CENTER_FREQUENCY` attribute specifies the frequency of the
    reference channel, expressed in Hz."""

    INBAND = 1
    r"""Specifies that the measurement is performed over all the channels as specified by the standard. For BR and EDR packets,
    79 channels starting from 2.402GHz to 2.48GHz are used for the measurement. For LE packets, 81 channels starting from
    2.401GHz to 2.481GHz are used for the measurement. In In-band mode, the Center Frequency attribute specifies the
    frequency of acquisition which must be equal to 2.441GHz. Configure the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_NUMBER` attribute to specify the frequency of the reference
    channel."""


class AcpReferenceChannelBandwidthMode(Enum):
    """AcpReferenceChannelBandwidthMode."""

    AUTO = 0
    r""""""

    MANUAL = 1
    r""""""


class AcpBurstSynchronizationType(Enum):
    """AcpBurstSynchronizationType."""

    NONE = 0
    r"""Specifies that the measurement does not perform synchronization to detect the start of the packet."""

    PREAMBLE = 1
    r"""Specifies that the measurement uses the preamble field bits to detect the start of the packet."""

    SYNC_WORD = 2
    r"""Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to
    detect the start of the packet. For BR /EDR packets, the sync word is derived from the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.BD_ADDRESS_LAP` attribute."""


class AcpAveragingEnabled(Enum):
    """AcpAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement uses the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_AVERAGING_COUNT` attribute as the number
    of acquisitions over which the ACP measurement is averaged."""


class AcpResultsMeasurementStatus(Enum):
    """AcpResultsMeasurementStatus."""

    NOT_APPLICABLE = -1
    r"""This attribute returns **Not Applicable** when you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **Symmetric**."""

    FAIL = 0
    r"""This attribute returns **Fail** if more than 3 offsets from offset 3 onwards fail the mask with exception or any offset
    channel fails the mask without exception."""

    PASS = 1
    r"""This attribute returns **Pass** if all offsets except up to a maximum of 3 from offset 3 onwards do not fail the mask
    with exception and all offset channels do not fail the mask without exception."""


class TwentydBBandwidthAveragingEnabled(Enum):
    """TwentydBBandwidthAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The 20dBBandwidth measurement uses the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_COUNT` attribute as the number of
    acquisitions over which the 20dBBandwidth measurement is averaged."""


class FrequencyRangeAveragingEnabled(Enum):
    """FrequencyRangeAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The FrequencyRange measurement uses the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.FREQUENCY_RANGE_AVERAGING_COUNT` attribute as the number of
    acquisitions over which the FrequencyRange measurement is averaged."""


class ModSpectrumBurstSynchronizationType(Enum):
    """ModSpectrumBurstSynchronizationType."""

    NONE = 0
    r"""Specifies that the measurement does not perform synchronization to detect the start of the packet."""

    PREAMBLE = 1
    r"""Specifies that the measurement uses the preamble field to detect the start of the packet."""

    SYNC_WORD = 2
    r"""Specifies that the measurement uses the Access Address for LE-CS packets to detect the start of the packet."""


class ModSpectrumAveragingEnabled(Enum):
    """ModSpectrumAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement uses the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODSPECTRUM_AVERAGING_COUNT` attribute as
    the number of acquisitions over which the ModSpectrum measurement is averaged."""


class TxpBurstSynchronizationType(Enum):
    """TxpBurstSynchronizationType."""

    NONE = 0
    r"""Specifies that the measurement does not perform synchronization to detect the start of the packet."""

    PREAMBLE = 1
    r"""Specifies that the measurement uses the preamble field to detect the start of the packet."""

    SYNC_WORD = 2
    r"""Specifies that the measurement uses sync word for the BR/EDR packets and access address for LE/LE-CS packets to detect
    the start of the packet. For BR /EDR packets, the sync word is derived from the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.BD_ADDRESS_LAP` attribute."""


class TxpAveragingEnabled(Enum):
    """TxpAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement uses the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_COUNT` attribute as the number
    of acquisitions over which the TXP measurement is averaged."""


class PowerRampBurstSynchronizationType(Enum):
    """PowerRampBurstSynchronizationType."""

    NONE = 0
    r"""Specifies that the measurement does not perform synchronization to detect the start of the packet."""

    PREAMBLE = 1
    r"""Specifies that the measurement uses the preamble field bits to detect the start of the packet."""

    SYNC_WORD = 2
    r"""Specifies that the measurement uses the Access Address for LE-CS packets to detect the start of the packet."""


class PowerRampAveragingEnabled(Enum):
    """PowerRampAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement uses the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_COUNT` attribute as the
    number of acquisitions over which the PowerRamp measurement is averaged."""


class LimitedConfigurationChange(Enum):
    """LimitedConfigurationChange."""

    DISABLED = 0
    r"""This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality
    attributes will be applied during RFmx Commit."""

    NO_CHANGE = 1
    r"""Signal configuration and RFmxInstr configuration are locked after the first Commit or Initiate of the named signal
    configuration. Any configuration change thereafter either in RFmxInstr attributes or personality attributes will not be
    considered by subsequent RFmx Commits or Initiates of this signal.  Use **No Change** if you have created named signal
    configurations for all measurement configurations but are setting some RFmxInstr attributes. Refer to the Limitations
    of the Limited Configuration Change Property topic for more details about the limitations of using this mode."""

    FREQUENCY = 2
    r"""Signal configuration, other than center frequency, external attenuation, and RFInstr configuration, is locked after
    first Commit or Initiate of the named signal configuration. Thereafter, only the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CENTER_FREQUENCY` and
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.EXTERNAL_ATTENUATION` attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal.  Refer to the Limitations of the Limited Configuration Change
    Property topic for more details about the limitations of using this mode."""

    REFERENCE_LEVEL = 3
    r"""Signal configuration, other than the reference level and RFInstr configuration, is locked after first Commit or
    Initiate of the named signal configuration. Thereafter only the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.REFERENCE_LEVEL` attribute value change will be considered by
    subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge
    Trigger, NI recommends that you set the
    :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` to **Relative** so that the trigger
    level is automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited
    Configuration Change Property topic for more details about the limitations of using this mode."""

    FREQUENCY_AND_REFERENCE_LEVEL = 4
    r"""Signal configuration, other than center frequency, reference level, external attenuation, and RFInstr configuration, is
    locked after first Commit or Initiate of the named signal configuration. Thereafter only Center Frequency, Reference
    Level, and External Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of
    this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power
    Edge  Level Type to **Relative** so that the trigger level is automatically adjusted as you adjust the reference level.
    Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of
    using this mode."""

    SELECTED_PORTS_FREQUENCY_AND_REFERENCE_LEVEL = 5
    r"""Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr
    configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected
    Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge
    Trigger, NI recommends you set the IQ Power Edge Level Type to **Relative** so that the trigger level is automatically
    adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic
    for more details about the limitations of using this mode."""


class Standard(Enum):
    """Standard."""

    BR = 0
    r""""""

    EDR = 0
    r""""""

    LE = 1
    r""""""

    LE_CS = 2
    r""""""


class MeasurementTypes(IntFlag):
    """MeasurementTypes."""

    TXP = 1 << 0
    r""""""

    MODACC = 1 << 1
    r""""""

    TWENTY_DB_BANDWIDTH = 1 << 2
    r""""""

    FREQUENCY_RANGE = 1 << 3
    r""""""

    ACP = 1 << 4
    r""""""

    POWERRAMP = 1 << 5
    r""""""

    MODSPECTRUM = 1 << 6
    r""""""
