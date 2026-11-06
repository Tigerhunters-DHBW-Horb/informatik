import unittest

from udp_gamepad_control_ui import command_from_gamepad


class GamepadCommandTests(unittest.TestCase):
    def test_left_stick_up_and_right_stick_turn(self):
        command = command_from_gamepad(0, (0.0, -1.0, 0.5, 0.0, 0.0), 0.3, 2.0, 1.5, 0.25)

        self.assertAlmostEqual(command.vx, 0.3)
        self.assertEqual(command.vy, 0.0)
        self.assertAlmostEqual(command.omega, (0.5 - 0.08) / 0.92 * 2.0)

    def test_deadzone_produces_zero_motion(self):
        command = command_from_gamepad(0, (0.04, -0.05, 0.06, 0.0, 0.0), 0.3, 2.0, 1.5, 0.25)

        self.assertEqual((command.vx, command.vy, command.omega), (0.0, 0.0, 0.0))

    def test_right_trigger_sprint_respects_firmware_cap(self):
        command = command_from_gamepad(0, (0.0, -1.0, 0.0, 0.0, 1.0), 0.4, 2.0, 2.0, 0.25)

        self.assertEqual(command.vx, 0.5)

    def test_left_trigger_sneak_takes_priority(self):
        command = command_from_gamepad(0, (0.0, -1.0, 0.0, 1.0, 1.0), 0.4, 2.0, 2.0, 0.25)

        self.assertEqual(command.vx, 0.1)


if __name__ == "__main__":
    unittest.main()
