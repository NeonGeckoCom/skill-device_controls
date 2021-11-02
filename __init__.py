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

import os

from enum import Enum
from neon_utils.message_utils import request_from_mobile
from adapt.intent import IntentBuilder
from random import randint
from mycroft_bus_client import Message
from neon_utils.skills.neon_skill import NeonSkill, LOG
from neon_utils.validator_utils import numeric_confirmation_validator

from mycroft import intent_handler

from .data_utils import refresh_neon


class SystemCommand(Enum):
    SHUTDOWN = "shut down this device"
    RESTART = "restart Neon"
    EXIT = "stop Neon"


class DeviceControlCenterSkill(NeonSkill):
    """
    Class name: DeviceControlCenterSkill

    Purpose: Provides control for most of the functionality of NeonX's device.

    Note: This skill would not proceed without the clear confirmation of
        the command from the user.
    """

    def __init__(self):
        super(DeviceControlCenterSkill, self).__init__(name="DeviceControlCenterSkill")

    def initialize(self):
        self.register_entity_file('dialogmode.entity')
        self.register_intent_file("change_dialog.intent", self.handle_change_dialog_option)

    def _do_exit_shutdown(self, action: SystemCommand):
        """
        Handle confirmed requests to stop running process.
        :param action: SystemCommand action to perform
        """
        if action == SystemCommand.SHUTDOWN:
            self.speak_dialog("ShuttingDown", private=True, wait=True)
            os.system("shutdown now -h")
        elif action == SystemCommand.EXIT:
            self.speak_dialog("Exiting", private=True, wait=True)
            self.bus.emit(Message("neon.shutdown"))

    @intent_handler(IntentBuilder("exit_shutdown_intent").require("RequestKeyword")
                    .one_of("exit", "shutdown"))
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
            elif message.data.get("restart"):  # TODO: Add 'restart' vocab DM
                action = SystemCommand.RESTART
            else:
                LOG.error("No exit or shutdown keyword! This shouldn't be possible")
                return
            response = self.get_response("ConfirmExitShutdown", {"action": action.value, "number": confirm_number},
                                         validator, "ActionNotConfirmed")
            if not response:
                self.speak_dialog("CancelExit", private=True)
            elif response:
                self._do_exit_shutdown(action)

    @intent_handler(IntentBuilder("skip_ww").optionally("neon").require("ww").require("start_sww"))
    @intent_handler(IntentBuilder("start_solo_mode").optionally("neon").require("start").require("solo"))
    def handle_skip_wake_words(self, message):
        """
        Disable wake words and start always-listening recognizer
        :param message: message object associated with request
        """
        if self.neon_in_request(message):
            if self.local_config.get("interface", {}).get("wake_word_enabled", True):
                resp = self.ask_yesno("AskStartSkipping")
                if resp == "yes":
                    self.speak_dialog("ConfirmSkipWW", private=True)
                    self.local_config.update_yaml_file("interface", "wake_word_enabled", False)
                    self.bus.emit(message.forward("neon.wake_words_state", {"enabled": False}))
                else:
                    self.speak_dialog("NotDoingAnything", private=True)
            else:
                self.speak_dialog("AlreadySkipping", private=True)

    @intent_handler(IntentBuilder("use_ww").optionally("neon").require("ww").require("stop_sww"))
    @intent_handler(IntentBuilder("stop_solo_mode").optionally("neon").require("stop").require("solo"))
    def handle_use_wake_words(self, message):
        """
        Enable wake words and stop always-listening recognizer
        :param message: message object associated with request
        """
        if not self.local_config.get("interface", {}).get("wake_word_enabled", False):
            resp = self.ask_yesno("AskStartRequiring")
            if resp == "yes":
                self.speak_dialog("ConfirmRequireWW", private=True)
                self.local_config.update_yaml_file("interface", "wake_word_enabled", True)
                self.bus.emit(message.forward("neon.wake_words_state", {"enabled": True}))
            else:
                self.speak_dialog("NotDoingAnything", private=True)
        else:
            self.speak_dialog("AlreadyRequiring", private=True)

    def handle_change_dialog_option(self, message):
        """
        Switch between primary and random dialog modes. Primary uses a fixed dialog for each skill, random uses options
        in the appropriate dialog file
        :param message:  message object associated with request
        """
        dialog_mode = message.data.get('utterance').lower()
        user = self.get_utterance_user(message)
        if self.voc_match(dialog_mode, "Primary"):
            dialog_mode = "primary"
        elif self.voc_match(dialog_mode, "Random"):
            dialog_mode = "random"
        else:
            LOG.error(f"No dialog mode found in: {message.data}")
            self.speak_dialog("DialogModeNotSpecified", private=True)
            return
        # TODO: This should use some configuration value, not signals. Probably per-user config DM
        if dialog_mode == "primary" and not self.check_for_signal("SKILLS_useDefaultResponses", -1):
            self.await_confirmation(user, "StartDefaultResponse")
            self.speak_dialog("ChangeDialog", {'mode': dialog_mode}, True, private=True)
        elif dialog_mode == "random" and self.check_for_signal("SKILLS_useDefaultResponses", -1):
            self.await_confirmation(user, "StartRandomResponse")
            self.speak_dialog("ChangeDialog", {'mode': dialog_mode}, True, private=True)
        else:
            self.speak_dialog("AlreadyInDialogMode", {"mode": dialog_mode}, private=True)

    @intent_handler(IntentBuilder("clear_data_intent").require("ClearKeyword").require("dataset")
                    .optionally("neon"))
    def handle_data_erase(self, message):
        """
        Handles a request to clear user data. This action will be confirmed numerically before executing
        :param message: message object associated with request
        """
        # TODO: Refactor this to use get_response, possibly spin off to separate skill DM
        opt = str(message.data.get('dataset')).replace("user ", "")
        confirm_number = randint(100, 999)
        # LOG.info(self.confirm_number)
        LOG.info(opt)
        if opt in ['of']:  # Catch bad regex parsing
            utt = message.data['utterance']
            LOG.info(utt)
            if " my " in utt:
                opt = utt.split("my ")[1]
            else:
                opt = utt
            LOG.info(opt)
        user = self.get_utterance_user(message)
        if self.voc_match(opt, "Selected"):
            to_clear = "clear your transcribed likes"
            self.await_confirmation(user, f"eraseSelectedTranscriptions_{confirm_number}")
        elif self.voc_match(opt, "Ignored"):
            to_clear = "clear your transcribed dislikes"
            self.await_confirmation(user, f"eraseIgnoredTranscriptions_{confirm_number}")
        elif self.voc_match(opt, "Transcription"):
            to_clear = "clear all of your transcriptions"
            self.await_confirmation(user, f"eraseAllTranscriptions_{confirm_number}")
        elif self.voc_match(opt, "Likes"):
            to_clear = "clear your liked brands"
            self.await_confirmation(user, [f"eraseSelectedTranscriptions_{confirm_number}",
                                           f"eraseLikes_{confirm_number}"])
        elif self.voc_match(opt, "Brands"):
            to_clear = "clear all of your brands"
            self.await_confirmation(user, [f"eraseSelectedTranscriptions_{confirm_number}",
                                           f"eraseIgnoredTranscriptions_{confirm_number}",
                                           f"eraseLikes_{confirm_number}",
                                           f"eraseIgnoredBrands_{confirm_number}"])
        elif self.voc_match(opt, "Data"):
            to_clear = "clear all of your data"
            self.await_confirmation(user, f"eraseAllData_{confirm_number}")
        elif self.voc_match(opt, "Media"):
            to_clear = "clear your user photos, videos, and audio recordings on this device"
            self.await_confirmation(user, f"eraseMedia_{confirm_number}")
        elif self.voc_match(opt, "Preferences"):
            to_clear = "reset your unit and interface preferences"
            self.await_confirmation(user, f"erasePrefs_{confirm_number}")
        elif self.voc_match(opt, "Language"):
            to_clear = "reset your language settings"
            self.await_confirmation(user, f"eraseLanguages_{confirm_number}")
        elif self.voc_match(opt, "Cache"):
            to_clear = "clear all of your cached responses"
            self.await_confirmation(user, f"eraseCache_{confirm_number}")
        elif self.voc_match(opt, "Profile"):
            to_clear = "reset your user profile"
            self.await_confirmation(user, f"eraseProfile_{confirm_number}")
        else:
            to_clear = None

        if to_clear:
            self.speak_dialog('ClearData', {'option': to_clear,
                                            'confirm': str(confirm_number)}, private=True)

    def converse(self, message=None):
        utterances = message.data.get("utterances")
        user = self.get_utterance_user(message)
        LOG.debug(f"check: {utterances}")
        LOG.debug(self.actions_to_confirm)
        if not utterances:
            return False
        if user in self.actions_to_confirm.keys():
            result = self.check_yes_no_response(message)
            LOG.debug(result)
            if result == -1:
                # This isn't a response, ignore it
                return False
            elif not result:
                # Response declined
                self.speak_dialog("NotDoingAnything", private=True)
                return True
            elif result:
                # Response confirmed (Either boolean True or string confirmation numbers
                actions_requested = self.actions_to_confirm.pop(user)
                LOG.debug(f"{user} confirmed action")
                if "StartDefaultResponse" in actions_requested:
                    self.create_signal("SKILLS_useDefaultResponses")
                    self.speak_dialog("ConfirmChangeDialog", {"mode": "primary responses"}, private=True)
                    # self.speak("Understood. I will use my primary responses to answer your requests.", private=True)
                elif "StartRandomResponse" in actions_requested:
                    self.check_for_signal("SKILLS_useDefaultResponses")
                    self.speak_dialog("ConfirmChangeDialog", {"mode": "dialog options"}, private=True)

                # Else this is a numeric confirmation with potentially multiple actions requested
                else:
                    # All actions for one user should have the same confirmation number, so just compare the first
                    confrimed_num = result
                    LOG.debug(f"Check if {confrimed_num} confirms: {actions_requested}")
                    if actions_requested[0].endswith(f"_{confrimed_num}"):
                        # Actions confirmed
                        user_dict = self.build_user_dict(message) if self.server else None

                        if f"eraseAllData_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear All")
                            self.speak_dialog("ConfirmClearAll", private=True)
                            # TODO: Non-server clear yml?
                            if self.server:
                                user_dict['ignored_brands'] = {}
                                user_dict['favorite_brands'] = {}
                                user_dict['specially_requested'] = {}
                                user_dict['first_name'] = ""
                                user_dict["middle_name"] = ""
                                user_dict["last_name"] = ""
                                user_dict["dob"] = "YYYY/MM/DD"
                                user_dict["age"] = ""
                                user_dict["email"] = ""
                                user_dict["picture"] = ""
                                user_dict["about"] = ""
                                user_dict["lat"] = 47.4799078
                                user_dict["lng"] = -122.2034496
                                user_dict["city"] = "Renton"
                                user_dict["state"] = "Washington"
                                user_dict["country"] = "America/Los_Angeles"
                                user_dict["time"] = 12
                                user_dict["date"] = "MDY"
                                user_dict["measure"] = "imperial"
                                user_dict["stt_language"] = "en"
                                user_dict["stt_region"] = "US"
                                user_dict["alt_languages"] = ['en']
                                user_dict["tts_language"] = "en-us"
                                user_dict["tts_gender"] = "female"
                                user_dict["neon_voice"] = "Joanna"
                                user_dict["secondary_tts_language"] = ""
                                user_dict["secondary_tts_gender"] = ""
                                user_dict["secondary_neon_voice"] = ""
                                user_dict["speed_multiplier"] = 1.0
                                # subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                                #                  + "/functions.sh; refreshNeon -A " + user_dict["username"]])
                                if request_from_mobile(message):
                                    self.mobile_skill_intent("clear_data", {"kind": "all"}, message)
                                else:
                                    self.socket_emit_to_server("clear cookies intent",
                                                               [message.context["klat_data"]["request_id"]])
                                refresh_neon("all", user)
                        if f"eraseSelectedTranscriptions_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear Selected Transcripts")
                            if f"eraseLikes_{confrimed_num}" in actions_requested:
                                self.speak_dialog("ConfirmClearData", {"kind": "likes"}, private=True)
                                # self.speak("Resetting your likes", private=True)
                                if self.server:
                                    user_dict['ignored_brands'] = {}
                                    user_dict['favorite_brands'] = {}
                                    user_dict['specially_requested'] = {}
                                else:
                                    self.user_config.update_yaml_file("brands", "ignored_brands", {}, True)
                                    self.user_config.update_yaml_file("brands", "favorite_brands", {}, True)
                                    self.user_config.update_yaml_file("brands", "specially_requested", {})
                            else:
                                self.speak("Taking care of your selected transcripts folder", private=True)
                            refresh_neon("selected", user)
                            # if self.server:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -S " + user_dict["username"]])
                            # else:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -s"])

                        if f"eraseIgnoredTranscriptions_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear Ignored Transcripts")
                            if f"eraseIgnoredBrands_{confrimed_num}" in actions_requested:
                                self.speak_dialog("ConfirmClearData", {"kind": "ignored brands"}, private=True)
                                # self.speak("Resetting ignored brands.", private=True)
                                if self.server:
                                    user_dict['ignored_brands'] = {}
                                else:
                                    self.user_config.update_yaml_file("brands", "ignored_brands", {})
                            else:
                                self.speak("Taking care of your ignored brands transcriptions", private=True)
                            refresh_neon("ignored", user)
                            # if self.server:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -I " + user_dict["username"]])
                            # else:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -i"])

                        if f"eraseAllTranscriptions_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear All Transcripts")
                            self.speak_dialog("ConfirmClearData", {"kind": "audio recordings and transcriptions"},
                                              private=True)
                            # self.speak("Audio recordings and transcriptions cleared", private=True)
                            refresh_neon("transcripts", user)
                            # if self.server:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -T " + user_dict["username"]])
                            #     if request_from_mobile(message):
                            #         self.mobile_skill_intent("clear_data", {"kind": "transcripts"}, message)
                            # else:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -t"])

                        if f"eraseProfile_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear Profile")
                            self.speak_dialog("ConfirmClearData", {"kind": "personal profile data"}, private=True)
                            # self.speak("Clearing your personal profile data.", private=True)
                            if self.server:
                                user_dict['first_name'] = ""
                                user_dict["middle_name"] = ""
                                user_dict["last_name"] = ""
                                user_dict["dob"] = "YYYY/MM/DD"
                                user_dict["age"] = ""
                                user_dict["email"] = ""
                                user_dict["picture"] = ""
                                user_dict["about"] = ""
                            else:
                                # TODO: Update user profile DM
                                pass
                                # subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                                #                  + "/functions.sh; refreshNeon -u"])

                        if f"eraseCache_{confrimed_num}" in actions_requested:
                            self.speak_dialog("ConfirmClearData", {"kind": "cached responses"}, private=True)
                            # if not self.server:
                            #     # self.speak("Clearing All cached responses.", private=True)
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -c"])
                            # else:
                            LOG.debug("Clear Caches")
                            if request_from_mobile(message):
                                self.mobile_skill_intent("clear_data", {"kind": "cache"}, message)
                            else:
                                self.socket_emit_to_server("clear cookies intent",
                                                           [message.context["klat_data"]["request_id"]])
                            refresh_neon("caches", user)

                        if f"erasePrefs_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear Preferences")
                            self.speak_dialog("ConfirmClearData", {"kind": "unit preferences"}, private=True)
                            # TODO: Update for non-server? DM
                            if self.server:
                                user_dict["time"] = 12
                                user_dict["date"] = "MDY"
                                user_dict["measure"] = "imperial"
                            # else:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -r"])
                            # self.speak("Resetting all interface preferences.", private=True)

                        if f"eraseMedia_{confrimed_num}" in actions_requested:
                            # Neon.clear_data(['p'])
                            self.speak_dialog("ConfirmClearData",
                                              {"kind": "pictures, videos, and audio recordings I have taken."},
                                              private=True)
                            # if self.server:
                            if request_from_mobile(message):
                                self.mobile_skill_intent("clear_data", {"kind": "media"}, message)
                            refresh_neon("media", user)
                            # else:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -p"])

                        if f"eraseLanguages_{confrimed_num}" in actions_requested:
                            self.speak_dialog("ConfirmClearData", {"kind": "language preferences"}, private=True)
                            # self.speak("Resetting your language preferences.", private=True)
                            # Neon.clear_data(['l'])
                            # TODO: Update for non-server? DM
                            if self.server:
                                user_dict["stt_language"] = "en"
                                user_dict["stt_region"] = "US"
                                user_dict["alt_languages"] = ['en']
                                user_dict["tts_language"] = "en-us"
                                user_dict["tts_gender"] = "female"
                                user_dict["neon_voice"] = "Joanna"
                                user_dict["secondary_tts_language"] = ""
                                user_dict["secondary_tts_gender"] = ""
                                user_dict["secondary_neon_voice"] = ""
                                user_dict["speed_multiplier"] = 1.0
                            # else:
                            #     subprocess.call(['bash', '-c', ". " + self.local_config["dirVars"]["ngiDir"]
                            #                      + "/functions.sh; refreshNeon -l"])

                        LOG.debug("DM: Clear Data Confirmed")
                        if self.server:
                            self.socket_emit_to_server("update profile", ["skill", user_dict,
                                                                          message.context["klat_data"]["request_id"]])
                        else:
                            self.bus.emit(Message('check.yml.updates',
                                                  {"modified": ["ngi_local_conf", "ngi_user_info"]},
                                                  {"origin": "device-control-center.neon"}))
                    else:
                        self.speak_dialog("ActionNotConfirmed", private=True)
                        # Reschedule event (resets timeout duration)
                        self.await_confirmation(user, actions_requested)

                return True

        return False

    def stop(self):
        self.clear_signals("DCC")


def create_skill():
    return DeviceControlCenterSkill()
