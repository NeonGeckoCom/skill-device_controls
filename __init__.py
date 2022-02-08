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

from enum import Enum
from adapt.intent import IntentBuilder
from random import randint
from mycroft_bus_client import Message
from neon_utils.skills.neon_skill import NeonSkill, LOG
from neon_utils.validator_utils import numeric_confirmation_validator

from mycroft.skills import intent_handler


class SystemCommand(Enum):
    SHUTDOWN = "shut down this device"
    RESTART = "restart Neon"
    EXIT = "stop Neon"


class DeviceControlCenterSkill(NeonSkill):
    def __init__(self):
        super(DeviceControlCenterSkill, self).__init__(name="DeviceControlCenterSkill")

    @intent_handler(IntentBuilder("exit_shutdown_intent").require("request")
                    .one_of("exit", "shutdown", "restart"))
    def handle_exit_shutdown_intent(self, message):
        """
        Handles a request to exit or shutdown. This action will be confirmed numerically before executing
        :param message: message object associated with request
        """
        if not self.server:
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
            response = self.get_response("ask_exit_shutdown", {"action": action.value, "number": confirm_number},
                                         validator, "action_not_confirmed")
            if not response:
                self.speak_dialog("confirm_cancel", private=True)
            elif response:
                self._do_exit_shutdown(action)

    @intent_handler(IntentBuilder("skip_ww").require("ww").require("start_sww"))
    @intent_handler(IntentBuilder("start_solo_mode").require("start").require("solo"))
    def handle_skip_wake_words(self, message):
        """
        Disable wake words and start always-listening recognizer
        :param message: message object associated with request
        """
        if self.neon_in_request(message):
            if self.local_config.get("interface", {}).get("wake_word_enabled", True):
                resp = self.ask_yesno("ask_start_skipping")
                if resp == "yes":
                    self.speak_dialog("confirm_skip_ww", private=True)
                    self.local_config.update_yaml_file("interface", "wake_word_enabled", False)
                    self.bus.emit(message.forward("neon.wake_words_state", {"enabled": False}))
                else:
                    self.speak_dialog("NotDoingAnything", private=True)
            else:
                self.speak_dialog("already_skipping", private=True)

    @intent_handler(IntentBuilder("use_ww").require("ww").require("stop_sww"))
    @intent_handler(IntentBuilder("stop_solo_mode").require("stop").require("solo"))
    def handle_use_wake_words(self, message):
        """
        Enable wake words and stop always-listening recognizer
        :param message: message object associated with request
        """
        if not self.local_config.get("interface", {}).get("wake_word_enabled", False):
            resp = self.ask_yesno("ask_start_requiring")
            if resp == "yes":
                self.speak_dialog("confirm_require_ww", private=True)
                self.local_config.update_yaml_file("interface", "wake_word_enabled", True)
                self.bus.emit(message.forward("neon.wake_words_state", {"enabled": True}))
            else:
                self.speak_dialog("NotDoingAnything", private=True)
        else:
            self.speak_dialog("already_requiring", private=True)

    def stop(self):
        pass

    def _do_exit_shutdown(self, action: SystemCommand):
        """
        Handle confirmed requests to stop running process.
        :param action: SystemCommand action to perform
        """
        if action == SystemCommand.SHUTDOWN:
            self.speak_dialog("confirm_shutdown", private=True, wait=True)
            os.system("shutdown now -h")
        elif action == SystemCommand.EXIT:
            self.speak_dialog("confirm_exiting", private=True, wait=True)
            self.bus.emit(Message("neon.shutdown"))
        elif action == SystemCommand.RESTART:
            self.speak_dialog("confirm_restarting", private=True, wait=True)
            self.bus.emit(Message("neon.restart"))
            # TODO: register a listener for this DM


def create_skill():
    return DeviceControlCenterSkill()
