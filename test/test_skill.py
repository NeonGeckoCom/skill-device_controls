# pylint: disable=protected-access,missing-docstring
# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
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
import tempfile
import unittest
from os.path import dirname
from threading import Event
from unittest.mock import Mock, patch

import pytest
from ovos_bus_client import Message
from ovos_utils.messagebus import FakeBus
from ovos_workshop.skill_launcher import SkillLoader
from skill_device_controls import DeviceControlCenterSkill

WW_STATE = True
bus = FakeBus()


def _ww_enabled(message):
    bus.emit(message.response({'enabled': WW_STATE}))


class TestSkill(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        bus.run_in_thread()
        bus.on('neon.query_wake_words_state', _ww_enabled)
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill: DeviceControlCenterSkill = skill_loader.instance

        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()

        # Mock exit/shutdown method to prevent interactions with test runner
        cls.skill._do_exit_shutdown = Mock()

        # Common wakeword configurations
        cls.single_ww = {"hey_neon": {"active": True}}
        cls.two_active_ww = {"hey_neon": {"active": True}, "hey_mycroft": {"active": True}}
        cls.one_in_two_active_ww = {"hey_neon": {"active": True}, "hey_mycroft": {"active": False}}
        cls.configured_but_not_active_ww = {"hey_neon": {"active": False}, "hey_mycroft": {"active": False}}

    def setUp(self):
        # For each test, create a unique temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Override the configuration and fs paths to use the temp directory
        self.skill.settings_write_path = self.temp_dir
        self.skill.file_system.path = self.temp_dir

        self.skill.speak.reset_mock()
        self.skill.speak_dialog.reset_mock()
        self.skill._do_exit_shutdown.reset_mock()

    def tearDown(self) -> None:
        self.skill.bus.remove_all_listeners("neon.wake_words_state")
        self.skill.bus.remove_all_listeners("neon.confirm_listening")
        self.skill.bus.remove_all_listeners("neon.show_debug")
        self.skill.bus.remove_all_listeners("neon.wake_words")
        self.skill.bus.remove_all_listeners("neon.get_wake_words")
        self.skill.bus.remove_all_listeners("neon.enable_wake_word")
        self.skill.bus.remove_all_listeners("neon.disable_wake_word")
        shutil.rmtree(self.temp_dir)

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)
        self.assertTrue(self.skill.ww_enabled)

    def test_handle_exit_shutdown_intent(self):
        # Exit Confirmed
        message = Message("valid_intent", {"exit": "exit"})

        def get_response(*args):
            self.assertEqual(args[0], "ask_exit_shutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ask_exit_shutdown")
            self.assertEqual(dialog_data["action"], "stop Neon")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "action_not_confirmed")
            return True

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill._do_exit_shutdown.assert_called()
        self.assertEqual(self.skill._do_exit_shutdown.call_args[0][0].name,
                         "EXIT")

        self.skill.get_response = default_get_response

        # Shutdown confirmed
        message = Message("valid_intent", {"shutdown": "shut down"})

        def get_response(*args):
            self.assertEqual(args[0], "ask_exit_shutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ask_exit_shutdown")
            self.assertEqual(dialog_data["action"], "shut down this device")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "action_not_confirmed")
            return True

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill._do_exit_shutdown.assert_called()
        self.assertEqual(self.skill._do_exit_shutdown.call_args[0][0].name,
                         "SHUTDOWN")

        self.skill.get_response = default_get_response

        # Restart Confirmed
        message = Message("valid_intent", {"restart": "reboot"})

        def get_response(*args):
            self.assertEqual(args[0], "ask_exit_shutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ask_exit_shutdown")
            self.assertEqual(dialog_data["action"], "restart Neon")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "action_not_confirmed")
            return True

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill._do_exit_shutdown.assert_called()
        self.assertEqual(self.skill._do_exit_shutdown.call_args[0][0].name,
                         "RESTART")

        self.skill.get_response = default_get_response

        # Exit Cancelled
        self.skill._do_exit_shutdown.reset_mock()
        message = Message("valid_intent", {"exit": "exit"})

        def get_response(*args):
            self.assertEqual(args[0], "ask_exit_shutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ask_exit_shutdown")
            self.assertEqual(dialog_data["action"], "stop Neon")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "action_not_confirmed")
            return False

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill.speak_dialog.assert_called_with("confirm_cancel", private=True)
        self.skill._do_exit_shutdown.assert_not_called()

        self.skill.get_response = default_get_response

        # Exit no response
        message = Message("valid_intent", {"exit": "exit"})

        def get_response(*args):
            self.assertEqual(args[0], "ask_exit_shutdown")
            dialog = args[0]
            dialog_data = args[1]
            validator = args[2]
            on_fail = args[3]

            self.assertEqual(dialog, "ask_exit_shutdown")
            self.assertEqual(dialog_data["action"], "stop Neon")
            confirm_number = dialog_data["number"]
            self.assertIsInstance(confirm_number, str)
            self.assertTrue(validator(confirm_number))
            self.assertFalse(validator(f"{confirm_number}0"))
            self.assertEqual(on_fail, "action_not_confirmed")
            return None

        default_get_response = self.skill.get_response
        self.skill.get_response = get_response
        self.skill.handle_exit_shutdown_intent(message)
        self.skill.speak_dialog.assert_called_with("confirm_cancel",
                                                   private=True)
        self.skill._do_exit_shutdown.assert_not_called()

        self.skill.get_response = default_get_response

    def test_handle_exit_intent(self):
        real_method = self.skill.handle_exit_shutdown_intent
        self.skill.handle_exit_shutdown_intent = Mock()
        msg = Message("test")
        self.skill.handle_exit_intent(msg)
        self.skill.handle_exit_shutdown_intent.assert_called_once_with(msg)
        self.assertTrue(msg.data.get('exit'))
        self.skill.handle_exit_shutdown_intent = real_method

    def test_handle_restart_intent(self):
        real_method = self.skill.handle_exit_shutdown_intent
        self.skill.handle_exit_shutdown_intent = Mock()
        msg = Message("test")
        self.skill.handle_restart_intent(msg)
        self.skill.handle_exit_shutdown_intent.assert_called_once_with(msg)
        self.assertTrue(msg.data.get('restart'))
        self.skill.handle_exit_shutdown_intent = real_method

    def test_handle_shutdown_intent(self):
        real_method = self.skill.handle_exit_shutdown_intent
        self.skill.handle_exit_shutdown_intent = Mock()
        msg = Message("test")
        self.skill.handle_shutdown_intent(msg)
        self.skill.handle_exit_shutdown_intent.assert_called_once_with(msg)
        self.assertTrue(msg.data.get('shutdown'))
        self.skill.handle_exit_shutdown_intent = real_method

    def test_handle_skip_wake_words_confirmed(self):
        global WW_STATE
        WW_STATE = True
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words",
                                           "start_sww": "begin"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": False})
            self.assertEqual(msg.context, message.context)
            global WW_STATE
            WW_STATE = False
            self.skill.bus.emit(msg.response())

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "ask_start_skipping")
            return "yes"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_skip_wake_words(message)
        self.skill.speak_dialog.assert_called_with("confirm_skip_ww",
                                                   private=True)
        self.assertTrue(called)
        self.assertFalse(self.skill.ww_enabled)

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_skip_wake_words_declined(self):
        global WW_STATE
        WW_STATE = True
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words",
                                           "start_sww": "begin"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": False})
            self.assertEqual(msg.context, message.context)
            self.skill.bus.emit(msg.response())

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "ask_start_skipping")
            return "no"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_skip_wake_words(message)
        self.skill.speak_dialog.assert_called_with("not_doing_anything",
                                                   private=True)
        self.assertFalse(called)
        self.assertTrue(self.skill.ww_enabled)

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_skip_wake_words_unconfirmed(self):
        global WW_STATE
        WW_STATE = True
        message = Message("valid_intent", {"neon": "Neon",
                                           "ww": "wake words",
                                           "start_sww": "begin"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": False})
            self.assertEqual(msg.context, message.context)
            self.skill.bus.emit(msg.response())

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "ask_start_skipping")
            return ""

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_skip_wake_words(message)
        self.skill.speak_dialog.assert_called_with("not_doing_anything",
                                                   private=True)
        self.assertFalse(called)
        self.assertTrue(self.skill.ww_enabled)

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_skip_wake_words_already_skipping(self):
        global WW_STATE
        WW_STATE = False
        message = Message("valid_intent", {"neon": "Neon", "ww": "wake words",
                                           "start_sww": "begin"},
                          {"test_context": "something"})
        self.skill.handle_skip_wake_words(message)
        self.skill.speak_dialog.assert_called_with("already_skipping",
                                                   private=True)

    def test_handle_use_wake_words_confirmed(self):
        global WW_STATE
        WW_STATE = False
        message = Message("valid_intent", {"neon": "Neon",
                                           "ww": "wake words",
                                           "stop_sww": "quit"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": True})
            self.assertEqual(msg.context, message.context)
            self.skill.bus.emit(msg.response())

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "ask_start_requiring")
            return "yes"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_use_wake_words(message)
        self.skill.speak_dialog.assert_called_with("confirm_require_ww",
                                                   private=True)
        self.assertTrue(called)

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_use_wake_words_declined(self):
        global WW_STATE
        WW_STATE = False
        message = Message("valid_intent", {"neon": "Neon",
                                           "ww": "wake words",
                                           "stop_sww": "quit"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": True})
            self.assertEqual(msg.context, message.context)
            self.skill.bus.emit(msg.response())

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "ask_start_requiring")
            return "no"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_use_wake_words(message)
        self.skill.speak_dialog.assert_called_with("not_doing_anything",
                                                   private=True)
        self.assertFalse(called)

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_use_wake_words_unconfirmed(self):
        global WW_STATE
        WW_STATE = False
        message = Message("valid_intent", {"neon": "Neon",
                                           "ww": "wake words",
                                           "stop_sww": "quit"},
                          {"test_context": "something"})

        called = False

        def on_wake_words_state(msg):
            nonlocal called
            called = True
            self.assertEqual(msg.msg_type, "neon.wake_words_state")
            self.assertEqual(msg.data, {"enabled": True})
            self.assertEqual(msg.context, message.context)
            self.skill.bus.emit(msg.response())

        def ask_yesno(*args):
            dialog = args[0]
            self.assertEqual(dialog, "ask_start_requiring")
            return "no"

        default_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = ask_yesno

        self.skill.bus.once("neon.wake_words_state", on_wake_words_state)

        self.skill.handle_use_wake_words(message)
        self.skill.speak_dialog.assert_called_with("not_doing_anything",
                                                   private=True)
        self.assertFalse(called)

        self.skill.ask_yesno = default_ask_yesno

    def test_handle_use_wake_words_already_requiring(self):
        global WW_STATE
        WW_STATE = True
        message = Message("valid_intent", {"neon": "Neon",
                                           "ww": "wake words",
                                           "stop_sww": "quit"},
                          {"test_context": "something"})
        self.skill.handle_use_wake_words(message)
        self.skill.speak_dialog.assert_called_with("already_requiring",
                                                   private=True)

    def test_handle_confirm_listening(self):
        listening_state = None
        update_event = Event()

        def handle_confirm_listening(msg):
            nonlocal listening_state
            listening_state = msg.data["enabled"]
            update_event.set()

        self.skill.bus.on("neon.confirm_listening", handle_confirm_listening)
        test_message = Message("test", {"enable": "turn on"})
        update_event.clear()
        self.skill.handle_confirm_listening(test_message)
        self.skill.speak_dialog.assert_called_with("confirm_listening_enabled")
        update_event.wait(3)
        self.assertTrue(listening_state)

        test_message = Message("test", {"disable": "disable"})
        update_event.clear()
        self.skill.handle_confirm_listening(test_message)
        self.skill.speak_dialog.assert_called_with("confirm_listening_disabled")
        update_event.wait(3)
        self.assertFalse(listening_state)

    def test_handle_show_debug(self):
        debug_state = None
        update_event = Event()

        def handle_show_debug(msg):
            nonlocal debug_state
            debug_state = msg.data["enabled"]
            update_event.set()

        self.skill.bus.on("neon.show_debug", handle_show_debug)
        test_message = Message("test", {"enable": "turn on"})
        update_event.clear()
        self.skill.handle_show_debug(test_message)
        self.skill.speak_dialog.assert_called_with("confirm_brain_enabled")
        update_event.wait(3)
        self.assertTrue(debug_state)

        test_message = Message("test", {"disable": "disable"})
        update_event.clear()
        self.skill.handle_show_debug(test_message)
        self.skill.speak_dialog.assert_called_with("confirm_brain_disabled")
        update_event.wait(3)
        self.assertFalse(debug_state)

    def test_handle_change_ww(self):
        wake_word_config = {"hey_mycroft": {"active": False},
                            "hey_neon": {"active": True}}

        message_change_hey_mycroft = Message("test",
                                             {"rx_wakeword": "hey mycroft"})
        message_change_hey_neon = Message("test", {"rx_wakeword": "Hey Neon"})
        message_change_invalid_ww = Message("test", {"rx_wakeword": "Nothing"})
        message_change_no_ww = Message("test",
                                       {"utterance": "change my wake word"})

        def _handle_get_ww(message):
            self.skill.bus.emit(message.reply("neon.wake_words",
                                              wake_word_config))

        # Test API not available
        self.skill.handle_change_ww(message_change_hey_neon)
        self.skill.speak_dialog.assert_called_with("error_no_ww_api", {"requested_ww": "hey neon"})
        self.skill.handle_change_ww(message_change_no_ww)
        self.skill.speak_dialog.assert_called_with("error_no_ww_api")

        self.skill.bus.on("neon.get_wake_words", _handle_get_ww)

        # Test no WW Requested
        self.skill.handle_change_ww(message_change_no_ww)
        self.skill.speak_dialog.assert_called_with("error_no_ww_heard")

        # Test invalid WW Requested
        self.skill.handle_change_ww(message_change_invalid_ww)
        self.skill.speak_dialog.assert_called_with("error_invalid_ww_requested",
                                                   {"requested_ww": "Nothing"})

        # Test already enabled
        self.skill.handle_change_ww(message_change_hey_neon)
        self.skill.speak_dialog.assert_called_with("error_ww_already_enabled",
                                                   {"requested_ww": "hey neon"})
        self.skill.speak_dialog.reset_mock()

        # Test already enabled alternate utterance
        message_change_hey_neon_alt = Message(
            "test", {"rx_wakeword": "haney on",
                     "utterance": "change my wakeword to haney on",
                     "utterances": [
                         "change my wakeword to haney on",
                         "change my wake word to hey neon"
                     ]})
        self.skill.handle_change_ww(message_change_hey_neon_alt)
        self.skill.speak_dialog.assert_called_with("error_ww_already_enabled",
                                                   {"requested_ww": "hey neon"})
        self.skill.speak_dialog.reset_mock()

        # Test already enabled voc match
        message_change_neon = Message(
            "test", {"rx_wakeword": "neon",
                     "utterance": "change my wakeword to neon",
                     "utterances": []})
        self.skill.handle_change_ww(message_change_neon)
        self.skill.speak_dialog.assert_called_with("error_ww_already_enabled",
                                                   {"requested_ww": "hey neon"})

        # Test change success
        def _handle_enable_ww(message):
            ww = message.data['wake_word']
            wake_word_config[ww]['active'] = True
            self.skill.bus.emit(message.response({"error": False,
                                                  "active": True,
                                                  "wake_word": ww}))

        def _handle_disable_ww(message):
            ww = message.data['wake_word']
            wake_word_config[ww]['active'] = False
            self.skill.bus.emit(message.response({"error": False,
                                                  "active": False,
                                                  "wake_word": ww}))

        self.skill.bus.on("neon.enable_wake_word", _handle_enable_ww)
        self.skill.bus.on("neon.disable_wake_word", _handle_disable_ww)

        self.skill.handle_change_ww(message_change_hey_mycroft)
        self.assertTrue(wake_word_config['hey_mycroft']['active'])
        self.assertFalse(wake_word_config['hey_neon']['active'])
        self.skill.speak_dialog.assert_called_with("confirm_ww_changed",
                                                   {"wake_word": "hey my-croft"})

        # Test already enabled, disable other
        wake_word_config['hey_neon']['active'] = True
        self.assertTrue(wake_word_config['hey_mycroft']['active'])
        self.assertTrue(wake_word_config['hey_neon']['active'])

        real_ask_yesno = self.skill.ask_yesno
        self.skill.ask_yesno = Mock(return_value="no")
        self.skill.handle_change_ww(message_change_hey_neon)
        self.skill.ask_yesno.assert_called_once_with("ask_disable_ww",
                                                     {"ww": "hey mycroft"})
        self.assertTrue(wake_word_config['hey_mycroft']['active'])
        self.assertTrue(wake_word_config['hey_neon']['active'])

        self.skill.ask_yesno.return_value = "yes"
        self.skill.handle_change_ww(message_change_hey_mycroft)
        self.skill.ask_yesno.assert_called_with("ask_disable_ww",
                                                {"ww": "hey neon"})
        self.skill.speak_dialog.assert_called_with("confirm_ww_disabled",
                                                   {"ww": "hey neon"})
        self.assertTrue(wake_word_config['hey_mycroft']['active'])
        self.assertFalse(wake_word_config['hey_neon']['active'])

        self.skill.ask_yesno = real_ask_yesno

        self.skill.bus.remove("neon.enable_wake_word", _handle_enable_ww)
        self.skill.bus.remove("neon.disable_wake_word", _handle_disable_ww)

        # Test change no response
        self.skill.handle_change_ww(message_change_hey_neon)
        self.skill.speak_dialog.assert_called_with("error_ww_change_failed")

        # Test change error response
        def _handle_enable_ww(message):
            self.skill.bus.emit(message.response({"error": True}))

        disable_ww = Mock()

        self.skill.bus.once("neon.enable_wake_word", _handle_enable_ww)
        self.skill.bus.once("neon.disable_wake_word", disable_ww)

        self.skill.handle_change_ww(message_change_hey_neon)
        self.skill.speak_dialog.assert_called_with("error_ww_change_failed")
        disable_ww.assert_not_called()

    def test_enable_ww(self):
        def _return_ww_none(message: Message):
            return None

        def _return_ww_error_response(message: Message):
            return message.response({"error": "error message"})

        def _return_ww_response(message: Message):
            self.skill.bus.emit(message.response({"ww": "hey_neon"}))

        self.skill.bus.once("neon.enable_wake_word", _return_ww_none)
        self.assertEqual(self.skill._enable_wake_word("hey_neon", Message("neon.enable_wake_word")), False)
        self.skill.bus.once("neon.enable_wake_word", _return_ww_error_response)
        self.assertEqual(self.skill._enable_wake_word("hey_neon", Message("neon.enable_wake_word")), False)
        self.skill.bus.once("neon.enable_wake_word", _return_ww_response)
        self.assertEqual(self.skill._enable_wake_word("hey_neon", Message("fake")), True)

    def test_disable_ww_none(self):
        def _return_ww_none(message: Message):
            return None
        self.skill.bus.once("neon.disable_wake_word", _return_ww_none)
        self.assertEqual(self.skill._disable_wake_word("hey_neon", Message("neon.disable_wake_word")), False)

    def test_disable_ww_error(self):
        def _return_ww_error_response(message: Message):
            return message.response({"error": "error message"})
        self.skill.bus.once("neon.disable_wake_word", _return_ww_error_response)
        self.assertEqual(self.skill._disable_wake_word("hey_neon", Message("neon.disable_wake_word")), False)

    def test_disable_ww_success(self):
        def _return_ww_response(message: Message):
            self.skill.bus.emit(message.response({"ww": "hey_neon"}))
        self.skill.bus.once("neon.disable_wake_word", _return_ww_response)
        self.assertEqual(self.skill._disable_wake_word("hey_neon", Message("fake")), True)


    def test_disable_all_ww(self):
        mock_get_ww = self.skill._get_wakewords = Mock()
        mock_get_enabled_ww = self.skill._get_enabled_wakewords = Mock()
        mock_disable_ww = self.skill._disable_wake_word = Mock()
        mock_speak_disabled_ww = self.skill._speak_disabled_ww_error = Mock()
        # if not available_ww, return False
        mock_get_ww.return_value = None
        self.assertFalse(self.skill._disable_all_wake_words(Message("test")))
        mock_get_ww.assert_called()
        mock_get_ww.reset_mock()
        # if available_ww, but none active
        mock_get_ww.return_value = {"hey_neon": {"active": True}}
        mock_get_enabled_ww.return_value = []
        self.assertFalse(self.skill._disable_all_wake_words(Message("test")))
        mock_get_ww.assert_called()
        mock_get_enabled_ww.assert_called()
        mock_get_enabled_ww.reset_mock()
        # if enabled_ww
        mock_get_enabled_ww.return_value = ["hey_neon"]
        # if success:
        mock_disable_ww.return_value = True
        self.assertTrue(self.skill._disable_all_wake_words(Message("test")))
        self.skill.speak_dialog.assert_called_once()
        # if failure:
        mock_disable_ww.reset_mock()
        mock_disable_ww.return_value = False
        self.assertFalse(self.skill._disable_all_wake_words(Message("test")))
        mock_speak_disabled_ww.assert_called()

    def test_get_wakewords_empty(self):
        def _return_empty_ww_response(message: Message):
            self.skill.bus.emit(message.response({}))

        self.skill.bus.once("neon.get_wake_words", _return_empty_ww_response)
        self.assertIsNone(self.skill._get_wakewords())

    def test_get_wakewords_basic(self):
        def _return_basic_ww_response(message: Message):
            self.skill.bus.emit(message.reply("neon.wake_words", self.single_ww, message.context))

        # return
        self.skill.bus.once("neon.get_wake_words", _return_basic_ww_response)
        self.assertEqual(self.single_ww, self.skill._get_wakewords())

    def test_get_wakewords_two_active(self):
        def _return_two_active_ww_response(message: Message):
            self.skill.bus.emit(message.reply("neon.wake_words", self.two_active_ww, message.context))

        self.skill.bus.once("neon.get_wake_words", _return_two_active_ww_response)
        self.assertEqual(self.two_active_ww, self.skill._get_wakewords())

    def test_get_wakewords_one_active_two_configured(self):
        def _return_one_active_two_configured_ww_response(message: Message):
            self.skill.bus.emit(message.reply("neon.wake_words", self.one_in_two_active_ww, message.context))

        self.skill.bus.once("neon.get_wake_words", _return_one_active_two_configured_ww_response)
        self.assertEqual(self.one_in_two_active_ww, self.skill._get_wakewords())

    def test_get_enabled_ww(self):
        # Single active wakeword
        self.assertListEqual(["hey_neon"], self.skill._get_enabled_wakewords(self.single_ww))
        # Two active wakewords
        self.assertListEqual(["hey_neon", "hey_mycroft"], self.skill._get_enabled_wakewords(self.two_active_ww))
        # Single active wakewords, two in config
        self.assertListEqual(["hey_neon"], self.skill._get_enabled_wakewords(self.one_in_two_active_ww))
        # No active wakewords, multiple in config
        self.assertListEqual([], self.skill._get_enabled_wakewords(self.configured_but_not_active_ww))

    @patch("ovos_config.models.MycroftSystemConfig")
    @patch("neon_core.patch_config")  # NOTE: Will not pass locally without Neon Core installed
    def test_handle_become_neon(self, mock_patch_config, mock_system_patch_config):
        self._set_user_neon_tts_settings = Mock()
        fake_message = Message("test")
        # no TTS config
        self.assertIsNone(self.skill.handle_become_neon(fake_message))
        mock_system_patch_config.assert_called()
        mock_system_patch_config.reset_mock()
        # TTS config, no default wakewords (invalid setting but we want to test for it)
        mock_config = {"tts": {"foo": {"bar": "baz"}}}
        mock_system_patch_config.return_value = mock_config
        self.assertIsNone(self.skill.handle_become_neon(fake_message))
        mock_system_patch_config.reset_mock()
        # TTS config, default wakewords
        mock_config = {"tts": {"foo": {"bar": "baz"}}, "hotwords": {"hey_neon": {"active": True}}}
        mock_system_patch_config.return_value = mock_config
        mock_patch_config.assert_called_with(mock_config)
        self._set_user_neon_tts_settings.assert_called()
        self.skill.speak_dialog.assert_called_with(fake_message)

    @patch("neon_core.patch_config")  # NOTE: Will not pass locally without Neon Core installed
    def test_set_jarvis_voice(self, mock_patch_config):
        jarvis_config = {
            "tts": {
                "module": "ovos-tts-plugin-mimic3-server",
                "ovos-tts-plugin-mimic3-server": {
                    "voice": "en_UK/apope_low",
                }
                # NOTE: There is no fallback because Neon Mk2 does not ship with Mimic3
            }
        }
        mock_patch_config.assert_called_with(jarvis_config)

    @patch("neon_utils.configuration_utils.NGIConfig.update_keys")
    def test_set_user_jarvis_tts_settings(self, mock_update_keys):
        self.skill._set_user_jarvis_tts_settings()
        mock_update_keys.assert_called_with({
            "speech": {
                "tts_language": "en_UK",
                "tts_gender": "male",
                "secondary_tts_gender": "male",
            }
        })

    @patch("neon_utils.configuration_utils.NGIConfig.update_keys")
    def test_set_user_neon_tts_settings(self, mock_update_keys):
        self.skill._set_user_neon_tts_settings()
        mock_update_keys.assert_called_with({
            "speech": {
                "tts_language": "en_US",
                "tts_gender": "female",
                "secondary_tts_gender": "female",
            }
        })


if __name__ == '__main__':
    pytest.main()
