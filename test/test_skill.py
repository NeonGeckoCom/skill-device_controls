# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import shutil
import unittest
import pytest

from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus


class TestSkill(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        from mycroft.skills.skill_loader import SkillLoader

        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs
        cls.skill._init_settings()
        cls.skill.initialize()
        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()
        # Mock exit/shutdown method to prevent interactions with test runner
        cls.skill._do_exit_shutdown = Mock()

    def setUp(self):
        self.skill.speak.reset_mock()
        self.skill.speak_dialog.reset_mock()
        self.skill._do_exit_shutdown.reset_mock()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_fs)

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)

    def test_exit_confirmed(self):
        message = Message("valid_intent", {"exit": "exit"})

        def get_response(*args):
            self.assertEqual(args[0], "ConfirmExitShutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ConfirmExitShutdown")
            self.assertEqual(dialog_data["action"], "stop Neon")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "ActionNotConfirmed")
            return True

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill._do_exit_shutdown.assert_called()
        self.assertEqual(self.skill._do_exit_shutdown.call_args[0][0].name, "EXIT")

        self.skill.get_response = default_get_response

    def test_shutdown_confirmed(self):
        message = Message("valid_intent", {"shutdown": "shut down"})

        def get_response(*args):
            self.assertEqual(args[0], "ConfirmExitShutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ConfirmExitShutdown")
            self.assertEqual(dialog_data["action"], "shut down this device")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "ActionNotConfirmed")
            return True

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill._do_exit_shutdown.assert_called()
        self.assertEqual(self.skill._do_exit_shutdown.call_args[0][0].name, "SHUTDOWN")

        self.skill.get_response = default_get_response

    def test_restart_confirmed(self):
        message = Message("valid_intent", {"restart": "reboot"})

        def get_response(*args):
            self.assertEqual(args[0], "ConfirmExitShutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ConfirmExitShutdown")
            self.assertEqual(dialog_data["action"], "restart Neon")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "ActionNotConfirmed")
            return True

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill._do_exit_shutdown.assert_called()
        self.assertEqual(self.skill._do_exit_shutdown.call_args[0][0].name, "RESTART")

        self.skill.get_response = default_get_response

    def test_exit_cancelled(self):
        message = Message("valid_intent", {"exit": "exit"})

        def get_response(*args):
            self.assertEqual(args[0], "ConfirmExitShutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ConfirmExitShutdown")
            self.assertEqual(dialog_data["action"], "stop Neon")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "ActionNotConfirmed")
            return False

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill.speak_dialog.assert_called_with("CancelExit", private=True)
        self.skill._do_exit_shutdown.assert_not_called()

        self.skill.get_response = default_get_response

    def test_exit_no_response(self):
        message = Message("valid_intent", {"exit": "exit"})

        def get_response(*args):
            self.assertEqual(args[0], "ConfirmExitShutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ConfirmExitShutdown")
            self.assertEqual(dialog_data["action"], "stop Neon")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "ActionNotConfirmed")
            return None

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill.speak_dialog.assert_called_with("CancelExit", private=True)
        self.skill._do_exit_shutdown.assert_not_called()

        self.skill.get_response = default_get_response


if __name__ == '__main__':
    pytest.main()
