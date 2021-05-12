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

import git
import glob
import os
import subprocess

from neon_utils.message_utils import request_from_mobile
from requests import HTTPError
from adapt.intent import IntentBuilder
from random import randint
from mycroft_bus_client import Message
from neon_utils.skills.neon_skill import NeonSkill, LOG

from .data_utils import refresh_neon
# from mycroft.skills.core import MycroftSkill
# from mycroft.messagebus.message import Message
# from mycroft.util.log import LOG


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

        do_update = IntentBuilder("update_neon").optionally("neon").require("update_neon").build()
        self.register_intent(do_update, self.handle_update_neon)

        self.register_intent_file("show_demo.intent", self.handle_show_demo)

        clear_data_intent = IntentBuilder("clear_data_intent").require("ClearKeyword").require("dataset").\
            optionally("neon").build()
        self.register_intent(clear_data_intent, self.handle_data_erase)

        exit_shutdown_intent = IntentBuilder("exit_shutdown_intent").require("RequestKeyword")\
            .one_of("Exit", "shutdown").optionally("neon").build()
        self.register_intent(exit_shutdown_intent, self.handle_exit_shutdown_intent)

        skip_ww_intent = IntentBuilder("skip_ww").optionally("neon").require("ww").require("start_sww").build()
        self.register_intent(skip_ww_intent, self.handle_skip_wake_words)

        use_ww_intent = IntentBuilder("use_ww").optionally("neon").require("ww").require("stop_sww").build()
        self.register_intent(use_ww_intent, self.handle_use_wake_words)

        # if not self.configuration_available["prefFlags"]["devMode"]:
        start_solo_intent = IntentBuilder("start_solo_mode").optionally("neon").require("start")\
            .require("solo").build()
        self.register_intent(start_solo_intent, self.handle_skip_wake_words)

        stop_solo_intent = IntentBuilder("stop_solo_mode").optionally("neon").require("stop")\
            .require("solo").build()
        self.register_intent(stop_solo_intent, self.handle_use_wake_words)

        # When first run or demo prompt not dismissed, wait for load and prompt user
        if self.local_config.get("prefFlags", {}).get("showDemo", False) and not self.server:
            self.bus.once('mycroft.ready', self._show_demo_prompt)
        elif self.local_config.get("prefFlags", {}).get("notifyRelease", False) and not self.server:
            self.bus.once('mycroft.ready', self._check_release)

    def _show_demo_prompt(self, message):
        """
        Handles first run demo prompt
        :param message: message object associated with loaded emit
        """
        LOG.debug("Prompting Demo!")
        self.make_active()
        self.await_confirmation(self.get_utterance_user(message), "startDemoPrompt", 600)
        self.speak("Would you like me to show you the demo of my abilities?",
                   expect_response=True, private=True)

    def _check_release(self, message):
        """
        Handles checking for a new release version
        :param message: message object associated with loaded emit
        """
        LOG.debug("Checking release!")
        resp = self.bus.wait_for_response(Message("neon.client.check_release"))
        if not resp:
            LOG.error(f"No response from server!")
            return False
        # TODO: Use versioning checks in neon_utils DM
        version_file = glob.glob(
            f'{self.local_config.get("dirVars", {}).get("ngiDir") or os.path.expanduser("~/.neon")}'
            f'/*.release')[0]
        version = os.path.splitext(os.path.basename(version_file))[0]  # 2009.0
        major, minor = version.split('.')
        new_major = resp.data.get("version_major", 0)
        new_minor = resp.data.get("version_minor", 0)
        # LOG.debug(str(result))
        if new_major > major or (new_major == major and new_minor > minor):
            # TODO: Dialog update when moved to packaged core DM
            # Server Reported Release Different than Install
            self.speak("There is a new release available from Neon Gecko. "
                       "Please pull changes on GitHub.", private=True, message=message)
            return True
        else:
            return False

    def handle_skip_wake_words(self, message):
        """
        Disable wake words and start always-listening recognizer
        :param message: message object associated with request
        """
        if self.neon_in_request(message):
            user = self.get_utterance_user(message)
            if self.local_config.get("interface", {}).get("wake_word_enabled", True):
                self.clear_signals("DCC")
                self.await_confirmation(user, "StartSWW")
                self.speak_dialog("AskStartSkipping", expect_response=True, private=True)
            else:
                self.speak_dialog("AlreadySkipping", private=True)

    def handle_use_wake_words(self, message):
        """
        Enable wake words and stop always-listening recognizer
        :param message: message object associated with request
        """
        if not self.local_config.get("interface", {}).get("wake_word_enabled", False):
            user = self.get_utterance_user(message)
            self.await_confirmation(user, "StopSWW")
            self.speak_dialog("AskStartRequiring", expect_response=True, private=True)
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

        if dialog_mode == "primary" and not self.check_for_signal("SKILLS_useDefaultResponses", -1):
            self.await_confirmation(user, "StartDefaultResponse")
            self.speak_dialog("ChangeDialog", {'mode': dialog_mode}, True, private=True)
        elif dialog_mode == "random" and self.check_for_signal("SKILLS_useDefaultResponses", -1):
            self.await_confirmation(user, "StartRandomResponse")
            self.speak_dialog("ChangeDialog", {'mode': dialog_mode}, True, private=True)
        else:
            self.speak_dialog("AlreadyInDialogMode", {"mode": dialog_mode}, private=True)
        # if dialog_mode is not None:
        #     if not any(x in dialog_mode for x in available_modes) and self.neon_in_request(message):
        #         self.speak("It looks like you did not specify which dialog "
        #                    "option you would like me to use.", private=True)
        #
        #         if not self.check_for_signal("SKILLS_useDefaultResponses", -1):
        #             self.await_confirmation(user, "StartDefaultResponse")
        #             dialog_mode = "primary"
        #         else:
        #             self.await_confirmation(user, "StartRandomResponse")
        #             dialog_mode = "random"
        #         self.speak_dialog("ChangeDialog", {'mode': dialog_mode}, True, private=True)
        #     else:
        #         if "random" in dialog_mode:
        #             dialog_mode = "random"
        #             self.await_confirmation(user, "StartRandomResponse")
        #         elif "default" in dialog_mode or "primary" in dialog_mode:
        #             dialog_mode = "primary"
        #             self.await_confirmation(user, "StartDefaultResponse")
        #         self.speak_dialog("ChangeDialog", {'mode': dialog_mode}, True, private=True)
        # else:
        #     LOG.error(f"No dialog mode found in: {message.data}")
        #     self.speak_dialog("DialogModeNotSpecified", private=True)

    def handle_update_neon(self, message):
        """
        Checks the version file on the git repository associated with this installation and compares to local version.
        If up to date, will check for a new release in the parent NeonGecko repository and notify user. User will
        be given the option to start an update in cases where there is an update available OR no new release available.
        :param message: message object associated with request
        """
        if self.neon_in_request(message) and not self.server:
            user = self.get_utterance_user(message)
            # if not self.server:
            self.clear_signals("DCC")
            if self.check_for_signal('CORE_useHesitation', -1):
                self.speak("Understood. Give me a moment to check for available updates.", private=True)
            current_version = self.local_config.get("devVars", {}).get("version", "0000-00-00")

            try:
                # TODO: Support packaged installations here DM
                if self.local_config["dirVars"].get("coreDir"):
                    new_version = git.Git(self.local_config["dirVars"]["coreDir"]).log(
                        "-1", "--format=%ai",
                        f'origin/{self.local_config.get("remoteVars", {}).get("coreBranch")}')
                    new_date, new_time, _ = new_version.split(" ", 2)
                    new_time = new_time.replace(":", "")
                    new_version = f"{new_date}-{new_time}"
                else:
                    # TODO: Read git from package data? DM
                    new_version = current_version
                LOG.info(f"New Version={new_version}")

                self.speak_dialog("CurrentVersion", {"version": str(current_version)}, private=True)
                if str(current_version) != str(new_version):
                    self.speak_dialog("UpdateAvailable", {"version": str(new_version)},
                                      expect_response=True, private=True)
                else:
                    if not self._check_release(message):
                        self.speak_dialog("AlreadyUpdated", private=True)
                        # self.await_confirmation(user, "initiateUpdate")
            except Exception as e:
                LOG.error(e)
                self.speak_dialog("ErrorCheckingVersion", private=True)
            self.await_confirmation(user, "initiateUpdate")

    def handle_show_demo(self, message):
        # TODO: This is very out of date. Update (maybe run script instead of using test function) DM
        """
        Starts the demoNeon shell script
        :param message: message object associated with request
        """
        if self.neon_in_request(message):
            if request_from_mobile(message):
                pass
            elif self.server:
                pass
            else:
                if self.check_for_signal('CORE_useHesitation', -1):
                    self.speak("Here you go", private=True)
                # import os
                # TODO: Make a new demo? DM
                os.chdir(self.local_config["dirVars"]["ngiDir"])
                os.system('gnome-terminal -- shortcuts/demoNeon.sh')

    def handle_exit_shutdown_intent(self, message):
        """
        Handles a request to exit or shutdown. This action will be confirmed numerically before executing
        :param message: message object associated with request
        """
        user = self.get_utterance_user(message)
        if not self.server:
            self.clear_signals("DCC")
            confirm_number = randint(100, 999)
            if message.data.get("Exit"):
                action = "stop me from running"
                self.await_confirmation(user, f"exitNow_{confirm_number}")
            elif message.data.get("shutdown"):
                action = "initiate full shutdown"
                self.await_confirmation(user, f"shutdownNow_{confirm_number}")
            else:
                LOG.error("No exit or shutdown keyword! This shouldn't be possible")
                return
            self.speak_dialog("ConfirmExitShutdown", {"action": action, "number": str(confirm_number)},
                              expect_response=True, private=True, wait=True)

    def handle_data_erase(self, message):
        """
        Handles a request to clear user data. This action will be confirmed numerically before executing
        :param message: message object associated with request
        """
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
                actions_requested = self.actions_to_confirm.pop(user)
                if "demoNextTime" in actions_requested:
                    self.speak_dialog("DemoNextTime", private=True)
                    self.local_config.update_yaml_file("prefFlags", "showDemo", False, final=True)

                elif "startDemoPrompt" in actions_requested:
                    self.await_confirmation(user, "demoNextTime")
                    self.speak_dialog("AskDemoNextTime", expect_response=True, private=True)
                elif any(opt in actions_requested for opt in ("shutdownNow", "exitNow")):
                    self.speak_dialog("CancelExit", private=True)
                else:  # No follow-up questions
                    self.speak_dialog("NotDoingAnything", private=True)
                return True
            elif result:
                # Response confirmed (Either boolean True or string confirmation numbers
                actions_requested = self.actions_to_confirm.pop(user)
                LOG.debug(f"{user} confirmed action")
                if "StartSWW" in actions_requested:
                    self.speak_dialog("ConfirmSkipWW", private=True)
                    self.local_config.update_yaml_file("interface", "wake_word_enabled", False)
                    self.bus.emit(message.forward("neon.wake_words_state", {"enabled": False}))
                    self.bus.emit(Message('check.yml.updates', {"modified": ["ngi_user_info"]},
                                          {"origin": "device-control-center.neon"}))
                elif "StopSWW" in actions_requested:
                    self.speak_dialog("ConfirmRequireWW", private=True)
                    self.local_config.update_yaml_file("interface", "wake_word_enabled", True)
                    self.bus.emit(message.forward("neon.wake_words_state", {"enabled": True}))
                    self.bus.emit(Message('check.yml.updates', {"modified": ["ngi_user_info"]},
                                          {"origin": "device-control-center.neon"}))
                elif "StartDefaultResponse" in actions_requested:
                    self.create_signal("SKILLS_useDefaultResponses")
                    self.speak_dialog("ConfirmChangeDialog", {"mode": "primary responses"}, private=True)
                    # self.speak("Understood. I will use my primary responses to answer your requests.", private=True)
                elif "StartRandomResponse" in actions_requested:
                    self.check_for_signal("SKILLS_useDefaultResponses")
                    self.speak_dialog("ConfirmChangeDialog", {"mode": "dialog options"}, private=True)
                    # self.speak("No problem. I will use my dialog options from now on", private=True)
                elif "startDemoPrompt" in actions_requested:
                    self.handle_show_demo(message)
                elif "demoNextTime" in actions_requested:
                    self.speak("Understood. I will ask again next time.", private=True)
                    self.local_config.update_yaml_file("prefFlags", "showDemo", True, final=True)

                elif "initiateUpdate" in actions_requested:
                    if not self.server:
                        self.speak("Starting the update.", private=True)
                        try:
                            os.chdir(self.local_config.get("dirVars", {}).get("ngiDir"))
                            subprocess.call(['gnome-terminal', '--', 'sudo', "./update.sh"])
                        except HTTPError as e:
                            LOG.info(e)

                # Else this is a numeric confirmation with potentially multiple actions requested
                else:
                    # All actions for one user should have the same confirmation number, so just compare the first
                    confrimed_num = result
                    LOG.debug(f"Check if {confrimed_num} confirms: {actions_requested}")
                    if actions_requested[0].endswith(f"_{confrimed_num}"):
                        # Actions confirmed
                        user_dict = self.build_user_dict(message) if self.server else None

                        if f"exitNow_{confrimed_num}" in actions_requested:
                            self.speak_dialog("Exiting", private=True, wait=True)
                            if not self.server:
                                self.bus.emit(Message("neon.shutdown"))
                                # subprocess.call([self.local_config["dirVars"]["coreDir"] + '/stop_neon.sh'])

                        if f"shutdownNow_{confrimed_num}" in actions_requested:
                            LOG.info('quiting')
                            self.speak("ShuttingDown", private=True, wait=True)
                            if not self.server:
                                os.system("shutdown now -h")

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
