import math
import struct
import unittest

from udp_sender import COMMAND, HEADER, MAGIC, PROTOCOL_VERSION, RobotCommand, encode_packet


class EncodePacketTests(unittest.TestCase):
    def test_encodes_commands_for_multiple_robot_ids(self):
        packet = encode_packet(
            [
                RobotCommand(2, 1.25, -0.5, 3.0),
                RobotCommand(7, 0.0, 2.0, -1.0),
            ],
            513,
        )

        self.assertEqual(len(packet), HEADER.size + 2 * COMMAND.size)
        self.assertEqual(
            HEADER.unpack_from(packet),
            (MAGIC, PROTOCOL_VERSION, 0, 513, 2),
        )
        self.assertEqual(
            COMMAND.unpack_from(packet, HEADER.size),
            (2, 1.25, -0.5, 3.0),
        )
        self.assertEqual(
            COMMAND.unpack_from(packet, HEADER.size + COMMAND.size),
            (7, 0.0, 2.0, -1.0),
        )

    def test_rejects_duplicate_ids_and_non_finite_values(self):
        with self.assertRaises(ValueError):
            encode_packet([RobotCommand(1, 0, 0, 0), RobotCommand(1, 1, 0, 0)], 0)
        with self.assertRaises(ValueError):
            encode_packet([RobotCommand(1, math.nan, 0, 0)], 0)
        with self.assertRaises(ValueError):
            encode_packet([RobotCommand(1, 1e100, 0, 0)], 0)

    def test_uses_network_byte_order(self):
        packet = encode_packet([RobotCommand(1, 1.0, 0.0, 0.0)], 0)
        expected = struct.pack("!4sBIHB", MAGIC, PROTOCOL_VERSION, 0, 0, 1)
        self.assertEqual(packet[: HEADER.size], expected)


if __name__ == "__main__":
    unittest.main()
