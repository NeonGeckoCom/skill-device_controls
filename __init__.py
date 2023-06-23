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

from typing import Optional
from enum import Enum
from adapt.intent import IntentBuilder
from random import randint
from ovos_bus_client import Message
from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from neon_utils.message_utils import dig_for_message
from neon_utils.skills.neon_skill import NeonSkill
from neon_utils.validator_utils import numeric_confirmation_validator

from mycroft.skills import intent_handler, intent_file_handler


class SystemCommand(Enum):
    SHUTDOWN = "shut down this device"
    RESTART = "restart Neon"
    EXIT = "stop Neon"


class DeviceControlCenterSkill(NeonSkill):
    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(network_before_load=False,
                                   internet_before_load=False,
                                   gui_before_load=False,
                                   requires_internet=False,
                                   requires_network=False,
                                   requires_gui=False,
                                   no_internet_fallback=True,
                                   no_network_fallback=True,
                                   no_gui_fallback=True)

    @property
    def ww_enabled(self) -> Optional[bool]:
        """
        Get the current wake words state.
        """
        resp = self.bus.wait_for_response(Message("neon.query_wake_words_state"))
        if not resp:
            LOG.warning("No WW Status reported")
            return None
        if resp.data.get('enabled', True):
            return True
        return False

    @property
    def wakewords(self) -> Optional[dict]:
        """
        Get a dict of available configured wake words.
        """
        message = dig_for_message() or Message("neon.get_wake_words")
        resp = self.bus.wait_for_response(
            message.forward("neon.get_wake_words"), "neon.wake_words")
        return resp.data if resp else None

    @intent_handler(IntentBuilder("ExitShutdownIntent").require("request")
                    .one_of("exit", "shutdown", "restart"))
    def handle_exit_shutdown_intent(self, message):
        """
        Handles a request to exit or shutdown.
        This action will be confirmed numerically before executing.
        :param message: message object associated with request
        """
        confirm_number = str(randint(100, 999))
        validator = numeric_confirmation_validator(confirm_number)
        if message.data.get("exit"):
            action = SystemCommand.EXIT
        elif message.data.get("shutdown"):
            action = SystemCommand.SHUTDOWN
        elif message.data.get("restart"):
            action = SystemCommand.RESTART
        else:
            LOG.error("No exit, shutdown, or restart keyword")
            return
        response = self.get_response("ask_exit_shutdown",
                                     {"action": action.value,
                                      "number": confirm_number},
                                     validator, "action_not_confirmed")
        if not response:
            self.speak_dialog("confirm_cancel", private=True)
        elif response:
            self._do_exit_shutdown(action)

    @intent_file_handler("exit.intent")
    def handle_exit_intent(self, message):
        message.data['exit'] = True
        self.handle_exit_shutdown_intent(message)

    @intent_file_handler("restart.intent")
    def handle_restart_intent(self, message):
        message.data['restart'] = True
        self.handle_exit_shutdown_intent(message)

    @intent_file_handler("shutdown.intent")
    def handle_shutdown_intent(self, message):
        message.data['shutdown'] = True
        self.handle_exit_shutdown_intent(message)

    @intent_handler(IntentBuilder("SkipWWIntent").require("ww")
                    .require("start_sww"))
    @intent_handler(IntentBuilder("SoloModeIntent").one_of("start", "enable")
                    .require("solo"))
    def handle_skip_wake_words(self, message):
        """
        Disable wake words and start always-listening recognizer
        :param message: message object associated with request
        """
        if self.neon_in_request(message):
            ww_state = self.ww_enabled
            if ww_state:
                resp = self.ask_yesno("ask_start_skipping")
                if resp == "yes":
                    self.speak_dialog("confirm_skip_ww", private=True)
                    self.bus.wait_for_response(message.forward(
                        "neon.wake_words_state", {"enabled": False}))
                else:
                    self.speak_dialog("not_doing_anything", private=True)
            else:
                self.speak_dialog("already_skipping", private=True)

    @intent_handler(IntentBuilder("UseWWIntent").require("ww")
                    .require("stop_sww"))
    @intent_handler(IntentBuilder("StopSoloModeIntent")
                    .one_of("stop", "disable").require("solo"))
    def handle_use_wake_words(self, message):
        """
        Enable wake words and stop always-listening recognizer
        :param message: message object associated with request
        """
        ww_state = self.ww_enabled
        if ww_state is False:  # If no return, assume WW always required
            resp = self.ask_yesno("ask_start_requiring")
            if resp == "yes":
                self.speak_dialog("confirm_require_ww", private=True)
                self.bus.wait_for_response(message.forward(
                    "neon.wake_words_state", {"enabled": True}))
            else:
                self.speak_dialog("not_doing_anything", private=True)
        else:
            self.speak_dialog("already_requiring", private=True)

    # TODO: Factory Reset

    @intent_handler(IntentBuilder("ConfirmListeningIntent")
                    .one_of("enable", "disable").require("listening").build())
    def handle_confirm_listening(self, message):
        """
        Enable confirmation sounds when a wake word is detected
        :param message: Message associated with request
        """
        enabled = True if message.data.get("enable") else False

        if enabled:
            self.speak_dialog("confirm_listening_enabled")
        else:
            self.speak_dialog("confirm_listening_disabled")
        self.bus.emit(message.forward("neon.confirm_listening",
                                      {"enabled": enabled}))
        # TODO: Handle this event DM

    @intent_handler(IntentBuilder("ShowDebugIntent")
                    .one_of("enable", "disable").require("debug").build())
    def handle_show_debug(self, message):
        enabled = True if message.data.get("enable") else False

        if enabled:
            self.speak_dialog("confirm_brain_enabled")
        else:
            self.speak_dialog("confirm_brain_disabled")
        self.bus.emit(message.forward("neon.show_debug",
                                      {"enabled": enabled}))
        # TODO: Handle this event DM

    @intent_handler(IntentBuilder("ChangeWakeWordIntent")
                    .require("change").require("ww").optionally("rx_wakeword"))
    def handle_change_ww(self, message):
        """
        Handle a user request to change their configured wake word.
        """
        requested_ww = message.data.get("rx_wakeword") or \
            message.data.get("utterance")
        available_ww = self.wakewords
        if not available_ww:
            LOG.warning(f"Wake Word API Not Available")
            self.speak_dialog("error_no_ww_api")
            return
        enabled_ww = [ww for ww in available_ww.keys() if
                      available_ww[ww].get('active')]
        matched_ww = None
        for ww in available_ww.keys():
            if ww.lower().replace('_', ' ') in requested_ww.lower():
                LOG.debug(f"matched: {ww}")
                matched_ww = ww
                break
        if not matched_ww:
            LOG.warning("Checking alternate transcriptions for a wake word")
            utterances = message.data.get('utterances', [])
            for ww in available_ww.keys():
                test_ww = ww.lower().replace('_', ' ')
                if any([test_ww in utt.lower() for utt in utterances]):
                    matched_ww = ww
                    LOG.debug(f"Found ww: {matched_ww}")
                    break
        if not matched_ww:
            LOG.warning("Checking for known wake words")
            if self.voc_match(requested_ww, 'mycroft') and \
                    'hey_mycroft' in available_ww.keys():
                matched_ww = 'hey_mycroft'
            elif self.voc_match(requested_ww, 'neon') and \
                    'hey_neon' in available_ww.keys():
                matched_ww = 'hey_neon'

        if not matched_ww:
            LOG.debug(f"No valid ww matched in: {requested_ww}")
            if message.data.get("rx_wakeword"):
                self.speak_dialog("error_invalid_ww_requested",
                                  {"requested_ww": requested_ww})
            else:
                self.speak_dialog("error_no_ww_heard")
            return
        if matched_ww in enabled_ww:
            self.speak_dialog("error_ww_already_enabled",
                              {"requested_ww": matched_ww.replace("_", " ")})
            if len(enabled_ww) > 1:
                LOG.info(f"Multiple WW active")
                for ww in enabled_ww:
                    if ww != matched_ww:
                        spoken_ww = ww.replace("_", " ")
                        resp = self.ask_yesno("ask_disable_ww",
                                              {"ww": spoken_ww})
                        if resp == "yes":
                            if self._disable_wake_word(ww, message):
                                self.speak_dialog("confirm_ww_disabled",
                                                  {"ww": spoken_ww})
                            else:
                                pass
                                # TODO: Speak error

            return

        self.speak_dialog("confirm_ww_changing")
        if not self._enable_wake_word(matched_ww, message):
            self.speak_dialog("error_ww_change_failed")
            # TODO: If this is a timeout, the new WW might be active
            return

        new_ww = matched_ww.replace('_', ' ')
        if "mycroft" in new_ww:
            LOG.debug("Patching 'mycroft' pronunciation")
            new_ww = new_ww.replace('mycroft', 'my-croft')
        if len(enabled_ww) == 1:
            old_ww = enabled_ww[0]
            LOG.debug(f"Disable old WW: {old_ww}")
            self._disable_wake_word(old_ww, message)
            # TODO: Something different if this fails

            self.speak_dialog("confirm_ww_changed", {"wake_word": new_ww})
        else:
            LOG.info(f"Added WW to enabled wake words: {enabled_ww}")
            self.speak_dialog("confirm_ww_changed", {"wake_word": new_ww})

    def stop(self):
        pass

    def _enable_wake_word(self, ww: str, message: Message) -> bool:
        """
        Enable the requested wake word and return True on success
        :param ww: string wake word to enable
        :returns: True on success, False on failure
        """
        # This has to reload the recognizer loop, so allow more time to respond
        resp = self.bus.wait_for_response(message.forward(
            "neon.enable_wake_word", {"wake_word": ww}), timeout=30)
        if not resp:
            LOG.error("No response to WW enable request")
            return False
        if resp.data.get('error'):
            LOG.warning(f"WW enable failed with response: {resp.data}")
            return False
        return True

    def _disable_wake_word(self, ww: str, message: Message) -> bool:
        """
        Disable the requested wake word and return True on success
        :param ww: string wake word to disable
        :returns: True on success, False on failure
        """
        resp = self.bus.wait_for_response(message.forward(
            "neon.disable_wake_word", {"wake_word": ww}), timeout=30)
        if not resp:
            LOG.error("No response to WW disable request")
            return False
        if resp.data.get('error'):
            LOG.warning(f"WW disable failed with response: {resp.data}")
            return False
        return True

    def _do_exit_shutdown(self, action: SystemCommand):
        """
        Handle confirmed requests to stop running process.
        :param action: SystemCommand action to perform
        """
        if action == SystemCommand.SHUTDOWN:
            self.speak_dialog("confirm_shutdown", private=True, wait=True)
            self.bus.emit(Message("system.shutdown"))
        elif action == SystemCommand.EXIT:
            self.speak_dialog("confirm_exiting", private=True, wait=True)
            self.bus.emit(Message("neon.shutdown"))
        elif action == SystemCommand.RESTART:
            self.speak_dialog("confirm_restarting", private=True, wait=True)
            self.bus.emit(Message("system.reboot"))
