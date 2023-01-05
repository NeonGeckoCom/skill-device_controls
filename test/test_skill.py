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

import os
import json
import shutil
import unittest
from threading import Event

import pytest

from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus

from mycroft.skills.skill_loader import SkillLoader


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
        cls.skill = skill_loader.instance

        # Define a directory to use for testing
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)

        # Override the configuration and fs paths to use the test directory
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs

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
        self.assertTrue(self.skill.ww_enabled)

    def test_handle_exit_shutdown_intent_exit_confirmed(self):
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

    def test_handle_exit_shutdown_intent_shutdown_confirmed(self):
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

    def test_handle_exit_shutdown_intent_restart_confirmed(self):
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

    def test_handle_exit_shutdown_intent_exit_cancelled(self):
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

    def test_handle_exit_shutdown_intent_exit_no_response(self):
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


class TestSkillLoading(unittest.TestCase):
    """
    Test skill loading, intent registration, and langauge support. Test cases
    are generic, only class variables should be modified per-skill.
    """
    # Static parameters
    bus = FakeBus()
    messages = list()
    test_skill_id = 'test_skill.test'
    # Default Core Events
    default_events = ["mycroft.skill.enable_intent",
                      "mycroft.skill.disable_intent",
                      "mycroft.skill.set_cross_context",
                      "mycroft.skill.remove_cross_context",
                      "intent.service.skills.deactivated",
                      "intent.service.skills.activated",
                      "mycroft.skills.settings.changed",
                      "skill.converse.ping",
                      "skill.converse.request",
                      f"{test_skill_id}.activate",
                      f"{test_skill_id}.deactivate"
                      ]

    # Import and initialize installed skill
    from skill_device_controls import DeviceControlCenterSkill
    skill = DeviceControlCenterSkill()

    # Specify valid languages to test
    supported_languages = ["en-us"]

    # Specify skill intents as sets
    adapt_intents = {'ExitShutdownIntent', 'SkipWWIntent', 'SoloModeIntent',
                     'UseWWIntent', 'StopSoloModeIntent',
                     'ConfirmListeningIntent', 'ShowDebugIntent'}
    padatious_intents = set()

    # regex entities, not necessarily filenames
    regex = set()
    # vocab is lowercase .voc file basenames
    vocab = {"debug", "disable", "enable", "exit", "listening", "no", "request",
             "restart", "shutdown", "solo", "start", "start_sww", "stop",
             "stop_sww", "ww"}
    # dialog is .dialog file basenames (case-sensitive)
    dialog = {"action_not_confirmed", "already_requiring", "already_skipping",
              "ask_exit_shutdown", "ask_start_requiring", "ask_start_skipping",
              "confirm_brain_disabled", "confirm_brain_enabled",
              "confirm_cancel", "confirm_exiting", "confirm_listening_disabled",
              "confirm_listening_enabled", "confirm_require_ww",
              "confirm_restarting", "confirm_shutdown", "confirm_skip_ww",
              "not_doing_anything"}

    @classmethod
    def setUpClass(cls) -> None:
        cls.bus.on("message", cls._on_message)
        cls.skill.config_core["secondary_langs"] = cls.supported_languages
        cls.skill._startup(cls.bus, cls.test_skill_id)
        cls.adapt_intents = {f'{cls.test_skill_id}:{intent}'
                             for intent in cls.adapt_intents}
        cls.padatious_intents = {f'{cls.test_skill_id}:{intent}'
                                 for intent in cls.padatious_intents}

    @classmethod
    def _on_message(cls, message):
        cls.messages.append(json.loads(message))

    def test_skill_setup(self):
        self.assertEqual(self.skill.skill_id, self.test_skill_id)
        for msg in self.messages:
            self.assertEqual(msg["context"]["skill_id"], self.test_skill_id)

    def test_intent_registration(self):
        registered_adapt = list()
        registered_padatious = dict()
        registered_vocab = dict()
        registered_regex = dict()
        for msg in self.messages:
            if msg["type"] == "register_intent":
                registered_adapt.append(msg["data"]["name"])
            elif msg["type"] == "padatious:register_intent":
                lang = msg["data"]["lang"]
                registered_padatious.setdefault(lang, list())
                registered_padatious[lang].append(msg["data"]["name"])
            elif msg["type"] == "register_vocab":
                lang = msg["data"]["lang"]
                if msg['data'].get('regex'):
                    registered_regex.setdefault(lang, dict())
                    regex = msg["data"]["regex"].split(
                        '<', 1)[1].split('>', 1)[0].replace(
                        self.test_skill_id.replace('.', '_'), '').lower()
                    registered_regex[lang].setdefault(regex, list())
                    registered_regex[lang][regex].append(msg["data"]["regex"])
                else:
                    registered_vocab.setdefault(lang, dict())
                    voc_filename = msg["data"]["entity_type"].replace(
                        self.test_skill_id.replace('.', '_'), '').lower()
                    registered_vocab[lang].setdefault(voc_filename, list())
                    registered_vocab[lang][voc_filename].append(
                        msg["data"]["entity_value"])
        self.assertEqual(set(registered_adapt), self.adapt_intents)
        for lang in self.supported_languages:
            if self.padatious_intents:
                self.assertEqual(set(registered_padatious[lang]),
                                 self.padatious_intents)
            if self.vocab:
                self.assertEqual(set(registered_vocab[lang].keys()), self.vocab)
            if self.regex:
                self.assertEqual(set(registered_regex[lang].keys()), self.regex)
            for voc in self.vocab:
                # Ensure every vocab file has at least one entry
                self.assertGreater(len(registered_vocab[lang][voc]), 0)
            for rx in self.regex:
                # Ensure every vocab file has exactly one entry
                self.assertTrue(all((rx in line for line in
                                     registered_regex[lang][rx])))

    def test_skill_events(self):
        events = self.default_events + list(self.adapt_intents)
        for event in events:
            self.assertIn(event, [e[0] for e in self.skill.events])

    def test_dialog_files(self):
        for lang in self.supported_languages:
            for dialog in self.dialog:
                file = self.skill.find_resource(f"{dialog}.dialog", "dialog",
                                                lang)
                self.assertTrue(os.path.isfile(file))


class TestSkillIntentMatching(unittest.TestCase):
    # Import and initialize installed skill
    from skill_device_controls import DeviceControlCenterSkill
    skill = DeviceControlCenterSkill()

    import yaml
    test_intents = join(dirname(__file__), 'test_intents.yaml')
    with open(test_intents) as f:
        valid_intents = yaml.safe_load(f)

    from mycroft.skills.intent_service import IntentService
    bus = FakeBus()
    intent_service = IntentService(bus)
    test_skill_id = 'test_skill.test'

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill.config_core["secondary_langs"] = list(cls.valid_intents.keys())
        cls.skill._startup(cls.bus, cls.test_skill_id)

    def test_intents(self):
        for lang in self.valid_intents.keys():
            for intent, examples in self.valid_intents[lang].items():
                intent_event = f'{self.test_skill_id}:{intent}'
                self.skill.events.remove(intent_event)
                intent_handler = Mock()
                self.skill.events.add(intent_event, intent_handler)
                for utt in examples:
                    if isinstance(utt, dict):
                        data = list(utt.values())[0]
                        utt = list(utt.keys())[0]
                    else:
                        data = list()
                    message = Message('test_utterance',
                                      {"utterances": [utt], "lang": lang})
                    self.intent_service.handle_utterance(message)
                    intent_handler.assert_called_once()
                    intent_message = intent_handler.call_args[0][0]
                    self.assertIsInstance(intent_message, Message)
                    self.assertEqual(intent_message.msg_type, intent_event)
                    for datum in data:
                        if isinstance(datum, dict):
                            name = list(datum.keys())[0]
                            value = list(datum.values())[0]
                        else:
                            name = datum
                            value = None
                        if name in intent_message.data:
                            # This is an entity
                            voc_id = name
                        else:
                            # We mocked the handler, data is munged
                            voc_id = f'{self.test_skill_id.replace(".", "_")}' \
                                     f'{name}'
                        self.assertIsInstance(intent_message.data.get(voc_id),
                                              str, intent_message.data)
                        if value:
                            self.assertEqual(intent_message.data.get(voc_id),
                                             value)
                    intent_handler.reset_mock()


if __name__ == '__main__':
    pytest.main()
