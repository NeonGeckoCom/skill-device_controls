# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2021 Neongecko.com Inc.
# BSD-3
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
