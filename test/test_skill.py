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
from neon_utils.configuration_utils import get_neon_local_config, get_neon_user_config

from mycroft.skills.skill_loader import SkillLoader


class TestSkill(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance

        # Define a directory to use for testing
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)

        # Override the configuration and fs paths to use the test directory
        cls.skill.local_config = get_neon_local_config(cls.test_fs)
        cls.skill.user_config = get_neon_user_config(cls.test_fs)
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

    def tearDown(self) -> None:
        self.skill.bus.remove_all_listeners("neon.wake_words_state")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_fs)

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)
        self.assertTrue(self.skill.local_config["interface"]["wake_word_enabled"])

    def test_handle_exit_shutdown_intent_exit_confirmed(self):
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

    def test_handle_exit_shutdown_intent_shutdown_confirmed(self):
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

    def test_handle_exit_shutdown_intent_restart_confirmed(self):
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

    def test_handle_exit_shutdown_intent_exit_cancelled(self):
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

    def test_handle_exit_shutdown_intent_exit_no_response(self):
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

    def test_handle_skip_wake_words_confirmed(self):
        self.skill.local_config["interface"]["wake_word_enabled"] = True
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words", "start_sww": "begin"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": False})
            self.assertEqual(msg.context, message.context)

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "AskStartSkipping")
            return "yes"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_skip_wake_words(message)
        self.skill.speak_dialog.assert_called_with("ConfirmSkipWW", private=True)
        self.assertTrue(called)
        self.assertFalse(self.skill.local_config["interface"]["wake_word_enabled"])

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_skip_wake_words_declined(self):
        self.skill.local_config["interface"]["wake_word_enabled"] = True
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words", "start_sww": "begin"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": False})
            self.assertEqual(msg.context, message.context)

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "AskStartSkipping")
            return "no"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_skip_wake_words(message)
        self.skill.speak_dialog.assert_called_with("NotDoingAnything", private=True)
        self.assertFalse(called)
        self.assertTrue(self.skill.local_config["interface"]["wake_word_enabled"])

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_skip_wake_words_unconfirmed(self):
        self.skill.local_config["interface"]["wake_word_enabled"] = True
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words", "start_sww": "begin"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": False})
            self.assertEqual(msg.context, message.context)

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "AskStartSkipping")
            return ""

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_skip_wake_words(message)
        self.skill.speak_dialog.assert_called_with("NotDoingAnything", private=True)
        self.assertFalse(called)
        self.assertTrue(self.skill.local_config["interface"]["wake_word_enabled"])

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_skip_wake_words_already_skipping(self):
        self.skill.local_config["interface"]["wake_word_enabled"] = False
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words", "start_sww": "begin"},
                          {"test_context": "something"})
        self.skill.handle_skip_wake_words(message)
        self.skill.speak_dialog.assert_called_with("AlreadySkipping", private=True)

    def test_handle_use_wake_words_confirmed(self):
        self.skill.local_config["interface"]["wake_word_enabled"] = False
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words", "stop_sww": "quit"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": True})
            self.assertEqual(msg.context, message.context)

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "AskStartRequiring")
            return "yes"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_use_wake_words(message)
        self.skill.speak_dialog.assert_called_with("ConfirmRequireWW", private=True)
        self.assertTrue(called)
        self.assertTrue(self.skill.local_config["interface"]["wake_word_enabled"])

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_use_wake_words_declined(self):
        self.skill.local_config["interface"]["wake_word_enabled"] = False
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words", "stop_sww": "quit"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": True})
            self.assertEqual(msg.context, message.context)

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "AskStartRequiring")
            return "no"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_use_wake_words(message)
        self.skill.speak_dialog.assert_called_with("NotDoingAnything", private=True)
        self.assertFalse(called)
        self.assertFalse(self.skill.local_config["interface"]["wake_word_enabled"])

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_use_wake_words_unconfirmed(self):
        self.skill.local_config["interface"]["wake_word_enabled"] = False
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words", "stop_sww": "quit"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": True})
            self.assertEqual(msg.context, message.context)

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "AskStartRequiring")
            return "no"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_use_wake_words(message)
        self.skill.speak_dialog.assert_called_with("NotDoingAnything", private=True)
        self.assertFalse(called)
        self.assertFalse(self.skill.local_config["interface"]["wake_word_enabled"])

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_use_wake_words_already_requiring(self):
        self.skill.local_config["interface"]["wake_word_enabled"] = True
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words", "stop_sww": "quit"},
                          {"test_context": "something"})
        self.skill.handle_use_wake_words(message)
        self.skill.speak_dialog.assert_called_with("AlreadyRequiring", private=True)


if __name__ == '__main__':
    pytest.main()
