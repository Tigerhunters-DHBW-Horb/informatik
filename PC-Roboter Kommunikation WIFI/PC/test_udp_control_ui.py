import unittest

from udp_control_ui import command_from_controls


class CommandFromControlsTests(unittest.TestCase):
    def test_no_controls_produce_a_stop_command(self):
        command = command_from_controls(3, set(), 1.0, 2.0)

        self.assertEqual((command.robot_id, command.vx, command.vy, command.omega), (3, 0, 0, 0))

    def test_opposing_controls_cancel_each_other(self):
        command = command_from_controls(0, {"x+", "x-", "omega+", "omega-"}, 1.0, 2.0)

        self.assertEqual((command.vx, command.vy, command.omega), (0, 0, 0))

    def test_diagonal_motion_is_limited_to_maximum_linear_speed(self):
        command = command_from_controls(1, {"x+", "y+"}, 0.6, 3.0)

        self.assertAlmostEqual(command.vx, 0.6 / 2**0.5)
        self.assertAlmostEqual(command.vy, 0.6 / 2**0.5)
        self.assertAlmostEqual((command.vx**2 + command.vy**2) ** 0.5, 0.6)

    def test_rotation_can_be_combined_with_translation(self):
        command = command_from_controls(0, {"x+", "omega-"}, 0.5, 2.5)

        self.assertEqual((command.vx, command.vy, command.omega), (0.5, 0, -2.5))


if __name__ == "__main__":
    unittest.main()
