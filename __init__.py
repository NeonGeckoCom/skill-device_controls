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

# import datetime
import time
import git
import glob
import os

from requests import HTTPError
from adapt.intent import IntentBuilder
from random import randint
from mycroft.skills.core import MycroftSkill
from mycroft.messagebus.message import Message
import subprocess
from mycroft.util.log import LOG


class DeviceControlCenterSkill(MycroftSkill):
    """
    Class name: DeviceControlCenterSkill

    Purpose: Provides control for most of the functionality of NeonX's device.

    Note: This skill would not proceed without the clear confirmation of
        the command from the user.
    """

    def __init__(self):
        super(DeviceControlCenterSkill, self).__init__(name="DeviceControlCenterSkill")
        # self.create_signal("CORE_startedSkillLoad")
        # self.confirm_number = randint(100, 999)
        # self.options_erase = ["transcript", "like", "brand", "transcripts", "likes", "brands", "selected", "ignored",
        #                       "transcriptions", "transcription", "media", "pictures and videos", "preferences",
        #                       "languages", "profile", "cached responses"]
        self.selected = ['selected', 'selected transcripts', 'selected transcriptions',
                         'selected transcript', 'selected transcription', 'transcribed likes']
        self.ignored = ['dislikes', 'ignored', 'ignored brands']
        self.transcription = ['transcripts', 'transcriptions', 'transcript', 'transcription']
        self.likes = ['like', 'likes', 'liked brands', 'brands i like', 'what i like']
        self.brands = ['brand', 'brands']
        self.data = ['data', 'info', 'information']
        self.media = ['pictures', 'picture', 'photos', 'photo', 'media', 'videos', 'video', 'pictures and videos']
        self.prefs = ['preferences', 'settings', 'options']
        self.langs = ['languages', 'language', 'language settings', 'language options', 'language preferences']
        self.cache = ['cached responses', 'caches', 'cache', 'cookies', 'cookie']
        self.prof = ['profile', 'account', 'account settings']

    def initialize(self):
        # self.check_for_signal("restartedFromSkill")
        # if self.check_for_signal('skip_wake_word', -1) and self.check_for_signal("Intent_overwrite_req"):
        #     self.handle_intent_overwrite()

        # self.register_entity_file('ww.entity')
        self.register_entity_file('dialogmode.entity')
        # self.register_entity_file('random_number.entity')

        # confirm_yes = IntentBuilder("confirm_yes").require("confirm_yes").build()
        # self.register_intent(confirm_yes, self.handle_confirm_yes)
        #
        # confirm_no = IntentBuilder("confirm_no").require("confirm_no").build()
        # self.register_intent(confirm_no, self.handle_confirm_no)

        # if not self.check_for_signal('skip_wake_word', -1):
        #     do_update = IntentBuilder("update_neon").require("update_neon").build()
        # else:
        do_update = IntentBuilder("update_neon").optionally("neon").require("update_neon").build()
        self.register_intent(do_update, self.handle_update_neon)

        self.register_intent_file("show_demo.intent", self.handle_show_demo)
        # self.register_intent_file("clear_user_data.intent", self.handle_data_erase)

        clear_data_intent = IntentBuilder("clear_data_intent").require("ClearKeyword").require("dataset").\
            optionally("neon").build()
        self.register_intent(clear_data_intent, self.handle_data_erase)

        exit_shutdown_intent = IntentBuilder("exit_shutdown_intent").require("RequestKeyword")\
            .one_of("Exit", "shutdown").optionally("neon").build()
        self.register_intent(exit_shutdown_intent, self.handle_exit_shutdown_intent)
        # self.register_intent_file("exit_shutdown.intent", self.handle_exit_intent)

        # confirm_numeric_intent = IntentBuilder("confirm_numeric_intent").require("ConfirmKeyword").build()
        # self.register_intent(confirm_numeric_intent, self.handle_random_numeric)
        # # self.register_intent_file("confirm_numeric.intent", self.handle_random_numeric)

        skip_ww_intent = IntentBuilder("skip_ww").optionally("neon").require("ww").require("start_sww").build()
        self.register_intent(skip_ww_intent, self.handle_start_skipping)

        use_ww_intent = IntentBuilder("use_ww").optionally("neon").require("ww").require("stop_sww").build()
        self.register_intent(use_ww_intent, self.handle_stop_skipping)

        if not self.configuration_available["prefFlags"]["devMode"]:
            start_solo_intent = IntentBuilder("start_solo_mode").optionally("neon").require("start")\
                .require("solo").build()
            self.register_intent(start_solo_intent, self.handle_start_skipping)

            stop_solo_intent = IntentBuilder("stop_solo_mode").optionally("neon").require("stop")\
                .require("solo").build()
            self.register_intent(stop_solo_intent, self.handle_stop_skipping)

        # name intent and build it:
        self.register_intent_file("change_dialog.intent", self.handle_change_dialog_option)

        # When first run or demo prompt not dismissed, wait for load and prompt user
        if self.configuration_available["prefFlags"]["showDemo"] and not self.server:
            self.bus.once('mycroft.ready', self._show_demo_prompt)
        elif self.configuration_available["prefFlags"]["notifyRelease"] and not self.server:
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
        # self.local_config.update_yaml_file("prefFlags", "showDemo", False, final=True)

    def _check_release(self, message):
        """
        Handles checking for a new release version
        :param message: message object associated with loaded emit
        """
        LOG.debug("Checking release!")
        resp = self.bus.wait_for_response(Message("neon.client.check_release"))
        version_file = glob.glob(f'{self.configuration_available["dirVars"]["ngiDir"]}/*.release')[0]
        version = os.path.splitext(os.path.basename(version_file))[0]  # 2009.0
        major, minor = version.split('.')
        new_major = resp.data.get("version_major", 0)
        new_minor = resp.data.get("version_minor", 0)
        # LOG.debug(str(result))
        if new_major > major or (new_major == major and new_minor > minor):
            # Server Reported Release Different than Install
            self.speak("There is a new release available from Neon Gecko. "
                       "Please pull changes on GitHub.", private=True, message=message)
            return True
        else:
            return False

    def handle_start_skipping(self, message):
        """
        Disable wake words and start always-listening recognizer
        :param message: message object associated with request
        """
        if self.neon_in_request(message):
            user = self.get_utterance_user(message)
            if not self.check_for_signal("CORE_skipWakeWord", -1):
                self.clear_signals("DCC")
                # self.enable_intent('confirm_yes')
                # self.enable_intent('confirm_no')
                # self.create_signal("DCC_StartSWWResponse")
                self.await_confirmation(user, "StartSWW")
                self.speak("Should I start skipping wake words?", True, private=True)  # TODO: Dialog file DM
                # self.request_check_timeout(30, ["confirm_yes", "confirm_no"])
                # if self.check_for_signal(str(self.confirm_number)):
                #     self.handle_confirm_no(message)
            else:
                self.speak("It looks like I am already skipping wake words.", private=True)

    def handle_stop_skipping(self, message):
        """
        Enable wake words and stop always-listening recognizer
        :param message: message object associated with request
        """
        if self.check_for_signal("CORE_skipWakeWord", -1):
            user = self.get_utterance_user(message)
            # self.clear_signals("DCC")
            # self.enable_intent('confirm_yes')
            # self.enable_intent('confirm_no')
            # self.create_signal('DCC_StopSkippingWW')
            self.await_confirmation(user, "StopSWW")
            self.speak("Should I start requiring wake words?", True, private=True)
            # self.request_check_timeout(30, ["confirm_yes", "confirm_no"])
            # if self.check_for_signal(str(self.confirm_number)):
            #     self.handle_confirm_no(message)
        else:
            self.speak("It appears I am already in my wake word mode.", private=True)

    def handle_change_dialog_option(self, message):
        """
        Switch between primary and random dialog modes. Primary uses a fixed dialog for each skill, random uses options
        in the appropriate dialog file
        :param message:  message object associated with request
        """
        dialog_mode = message.data.get('utterance').lower()
        available_modes = "random", "default", "primary"  # TODO: Move to voc file matching DM
        user = self.get_utterance_user(message)
        if dialog_mode is not None:
            if not any(x in dialog_mode for x in available_modes) and self.neon_in_request(message):
                self.speak("It looks like you did not specify which dialog "
                           "option you would like me to use.", private=True)

                if not self.check_for_signal("SKILLS_useDefaultResponses", -1):
                    # self.create_signal("DCC_StartDefaultResponse")
                    self.await_confirmation(user, "StartDefaultResponse")
                    dialog_mode = "primary"
                    # self.speak("Would you like me to switch to primary responses?", True, private=True)
                else:
                    # self.create_signal("DCC_StartRandomResponse")
                    self.await_confirmation(user, "StartRandomResponse")
                    dialog_mode = "random"
                    # self.speak("Would you like me to start using random responses again?", True, private=True)
                self.speak_dialog("ChangeDialog", {'mode': dialog_mode}, True, private=True)
            else:
                # LOG.info(dialog_mode)
                # TODO: Handle already in mode here (currently in confirmation) DM
                if "random" in dialog_mode:
                    dialog_mode = "random"
                    self.await_confirmation(user, "StartRandomResponse")
                elif "default" in dialog_mode or "primary" in dialog_mode:
                    dialog_mode = "primary"
                    self.await_confirmation(user, "StartDefaultResponse")
                # self.speak("Would you like me to initiate " + str(dialog_mode) + "?", True)
                self.speak_dialog("ChangeDialog", {'mode': dialog_mode}, True, private=True)

            # Start timeout after Neon is done speaking to allow time for user to respond
            # self.request_check_timeout(30, ["confirm_yes", "confirm_no"])

            # if self.check_for_signal(str(self.confirm_number)):
            #     self.handle_confirm_no(message)
        else:
            LOG.error(f"No dialog mode found in: {message.data}")
            self.speak("I am not quite sure that I understand "
                       "which dialog mode you are asking me to use."
                       " Please let me try again and repeat your request.", private=True)

    def handle_update_neon(self, message):
        """
        Checks the version file on the git repository associated with this installation and compares to local version.
        If up to date, will check for a new release in the parent NeonGecko repository and notify user. User will
        be given the option to start an update in cases where there is an update available OR no new release available.
        :param message: message object associated with request
        """
        # if (self.check_for_signal("skip_wake_word", -1) and message.data.get("Neon")) \
        #         or not self.check_for_signal("skip_wake_word", -1) or self.check_for_signal("CORE_neonInUtterance"):
        if self.neon_in_request(message):
            user = self.get_utterance_user(message)
            if not self.server:
                # import os
                self.clear_signals("DCC")
                if self.check_for_signal('CORE_useHesitation', -1):
                    self.speak("Understood. Give me a moment to check for available updates.", private=True)
                # os.system(f"sudo {self.configuration_available['dirVars']['ngiDir']}/update.sh -v")
                # | "
                # f"tee -a {self.configuration_available['dirVars']['logsDir']}/update.log")
                current_version = self.configuration_available["devVars"]["version"]
                # os.chdir(self.configuration_available["dirVars"]["tempDir"])

                try:
                    new_version = git.Git(self.configuration_available["dirVars"]["coreDir"]).log(
                        "-1", "--format=%ai",
                        f'origin/{self.configuration_available["remoteVars"]["coreBranch"]}')
                    new_date, new_time, _ = new_version.split(" ", 2)
                    new_time = new_time.replace(":", "")
                    new_version = f"{new_date}--{new_time}"
                    LOG.info(f"New Version={new_version}")
                    # new_version = os.path.splitext(glob.glob('*.version')[0])[0]
                    # os.remove(str(glob.glob('*.version')[0]))
                    # self.enable_intent('confirm_yes')
                    # self.enable_intent('confirm_no')
                    # self.create_signal("DCC_initiateUpdate")

                    self.speak("I am on version " + str(current_version), private=True)
                    if str(current_version) != str(new_version):
                        self.speak("The most recent version is " + str(new_version) +
                                   "; would you like to install it now?", True, private=True)
                        self.await_confirmation(user, "initiateUpdate")
                    else:
                        if not self._check_release(message):
                            self.speak("I am already up to date, would you like to run the update anyway?",
                                       private=True)
                            self.await_confirmation(user, "initiateUpdate")

                except Exception as e:
                    LOG.error(e)
                    self.speak("I could not get the current version info, would you like to run the update anyway?",
                               private=True)

                # self.request_check_timeout(30, ["confirm_yes", "confirm_no"])
                # if self.check_for_signal(str(self.confirm_number)):
                #     self.handle_confirm_no(message)
        # else:
        #     self.check_for_signal("CORE_andCase")

    def handle_show_demo(self, message):
        # TODO: This is very out of date. Update (maybe run script instead of using test function) DM
        """
        Starts the demoNeon shell script
        :param message: message object associated with request
        """
        # if (self.check_for_signal("skip_wake_word", -1) and message.data.get("Neon")) \
        #         or not self.check_for_signal("skip_wake_word", -1) or self.check_for_signal("CORE_neonInUtterance"):
        if self.neon_in_request(message):
            if self.request_from_mobile(message):
                pass
            elif self.server:
                pass
            else:
                if self.check_for_signal('CORE_useHesitation', -1):
                    self.speak("Here you go", private=True)
                # import os
                os.chdir(self.configuration_available["dirVars"]["ngiDir"])
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
            # LOG.info("Hear you")
            if message.data.get("Exit"):
                action = "stop me from running"
                # self.speak("Are you sure that you wish to stop me from running?", private=True)
                # self.create_signal("DCC_exitNow")
                self.await_confirmation(user, f"exitNow_{confirm_number}")
            elif message.data.get("shutdown"):
                action = "initiate full shutdown"
                # self.speak("Are you sure that you wish to initiate full shutdown?", private=True)
                # self.create_signal("DCC_shutdownNow")
                self.await_confirmation(user, f"shutdownNow_{confirm_number}")
            else:
                LOG.error("No exit or shutdown keyword! This shouldn't be possible")
                return

            self.speak_dialog("ConfirmExitShutdown", {"action": action, "number": str(confirm_number)},
                              expect_response=True, private=True, wait=True)
            # self.enable_intent('confirm_no')
            # self.enable_intent('confirm_numeric_intent')
            # self.enable_intent('confirm_numeric.intent')
            # self.request_check_timeout(30, ["confirm_numeric_intent", "confirm_no"])
            # if self.check_for_signal(str(self.confirm_number)):
            #     self.handle_confirm_no(message)

    def handle_data_erase(self, message):
        """
        Handles a request to clear user data. This action will be confirmed numerically before executing
        :param message: message object associated with request
        """
        # uttr = message.data.get('utterance')
        # options = [x for x in self.options_erase if x in uttr]
        # LOG.info(uttr)
        # LOG.info(options)
        # if (self.check_for_signal("skip_wake_word", -1) and message.data.get("Neon")) \
        #         or not self.check_for_signal("skip_wake_word", -1):
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
        # self.clear_signals("DCC")
        # prefix = "DCC"
        # if self.server:
        #     user = self.preference_user(message)['username']
        #     self.clear_signals(f"{user}_DCC_")
        #     self.create_signal(f"{user}_DCC_{self.confirm_number}")
        #     prefix = f"{user}_DCC"
        user = self.get_utterance_user(message)
        if opt in self.selected:
            to_clear = "clear your transcribed likes"
            # self.create_signal(f"{prefix}_eraseSelectedTranscriptions")
            self.await_confirmation(user, f"eraseSelectedTranscriptions_{confirm_number}")
        elif opt in self.ignored:
            to_clear = "clear your transcribed dislikes"
            # self.create_signal(f"{prefix}_eraseIgnoredTranscriptions")
            self.await_confirmation(user, f"eraseIgnoredTranscriptions_{confirm_number}")
        elif opt in self.transcription:
            to_clear = "clear all of your transcriptions"
            # self.create_signal(f"{prefix}_eraseAllTranscriptions")
            self.await_confirmation(user, f"eraseAllTranscriptions_{confirm_number}")
        elif opt in self.likes:
            to_clear = "clear your liked brands"
            # self.create_signal(f"{prefix}_eraseSelectedTranscriptions")
            # self.create_signal(f"{prefix}_eraseLikes")
            self.await_confirmation(user, [f"eraseSelectedTranscriptions_{confirm_number}",
                                           f"eraseLikes_{confirm_number}"])
        elif opt in self.brands:
            to_clear = "clear all of your brands"
            # self.create_signal(f"{prefix}_eraseSelectedTranscriptions")
            # self.create_signal(f"{prefix}_eraseIgnoredTranscriptions")
            # self.create_signal(f"{prefix}_eraseLikes")
            # self.create_signal(f"{prefix}_eraseIgnoredBrands")
            self.await_confirmation(user, [f"eraseSelectedTranscriptions_{confirm_number}",
                                           f"eraseIgnoredTranscriptions_{confirm_number}",
                                           f"eraseLikes_{confirm_number}",
                                           f"eraseIgnoredBrands_{confirm_number}"])
        elif opt in self.data:
            to_clear = "clear all of your data"
            # self.create_signal(f"{prefix}_eraseAllData")
            self.await_confirmation(user, f"eraseAllData_{confirm_number}")
        elif opt in self.media:
            to_clear = "clear your user photos, videos, and audio recordings on this device"
            # self.create_signal(f"{prefix}_eraseMedia")
            self.await_confirmation(user, f"eraseMedia_{confirm_number}")
        elif opt in self.prefs:
            to_clear = "reset your unit and interface preferences"
            # self.create_signal(f"{prefix}_erasePrefs")
            self.await_confirmation(user, f"erasePrefs_{confirm_number}")
        elif opt in self.langs:
            to_clear = "reset your language settings"
            # self.create_signal(f"{prefix}_eraseLanguages")
            self.await_confirmation(user, f"eraseLanguages_{confirm_number}")
        elif opt in self.cache:
            to_clear = "clear all of your cached responses"
            # self.create_signal(f"{prefix}_eraseCache")
            self.await_confirmation(user, f"eraseCache_{confirm_number}")
        elif opt in self.prof:
            to_clear = "reset your user profile"
            # self.create_signal(f"{prefix}_eraseProfile")
            self.await_confirmation(user, f"eraseProfile_{confirm_number}")
        else:
            to_clear = None

        if to_clear:
            self.speak_dialog('ClearData', {'option': to_clear,
                                            'confirm': str(confirm_number)}, private=True)
            # self.enable_intent('confirm_no')
            # self.enable_intent('confirm_numeric_intent')
            # self.enable_intent('confirm_numeric.intent')
            # self.request_check_timeout(30, ["confirm_numeric_intent", "confirm_no"])
            # if self.check_for_signal(str(self.confirm_number)):
            #     LOG.info("Nothing said")
            #     self.handle_confirm_no(message)

    def converse(self, utterances, lang="en-us", message=None):
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
                    self.speak("Should I ask you next time?", True, private=True)
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
                    from NGI.utilities.utilHelper import NeonHelpers
                    self.speak("Okay, starting to skip wake words.", False, private=True)
                    time.sleep(1)
                    NeonHelpers.disable_ww()
                elif "StopSWW" in actions_requested:
                    from NGI.utilities.utilHelper import NeonHelpers
                    self.speak("Okay, entering wake words mode.", False, private=True)
                    time.sleep(1)
                    NeonHelpers.enable_ww()
                elif "StartDefaultResponse" in actions_requested:
                    if not self.check_for_signal("SKILLS_useDefaultResponses", -1):
                        self.create_signal("SKILLS_useDefaultResponses")
                        self.speak("Understood. I will use my primary responses to answer your requests.", private=True)
                    else:
                        self.speak("I am already using my primary responses. Try asking me something else.",
                                   private=True)
                elif "StartRandomResponse" in actions_requested:
                    if not self.check_for_signal("SKILLS_useDefaultResponses", -1):
                        self.speak("I am already using my random responses", private=True)
                    else:
                        self.check_for_signal("SKILLS_useDefaultResponses")
                        self.speak("No problem. I will use my dialog options from now on", private=True)
                elif "startDemoPrompt" in actions_requested:
                    self.handle_show_demo(message)
                elif "demoNextTime" in actions_requested:
                    self.speak("Understood. I will ask again next time.", private=True)
                    self.local_config.update_yaml_file("prefFlags", "showDemo", True, final=True)

                elif "initiateUpdate" in actions_requested:
                    if not self.server:
                        self.speak("Starting the update.", private=True)
                        try:
                            # import os
                            os.chdir(self.configuration_available["dirVars"]["ngiDir"])
                            # self.create_signal("update_from_skill")
                            subprocess.call(['gnome-terminal', '--', 'sudo', "./update.sh"])
                            # self.speak("Updates complete. I may need to restart. Please stay with me")
                            # self.emitter.emit(Message('configuration.updated'))

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
                            self.speak("Hope to see you again soon. Goodbye.", private=True)
                            time.sleep(3)
                            if not self.server:
                                subprocess.call([self.configuration_available["dirVars"]["coreDir"] + '/stop_neon.sh'])

                        if f"shutdownNow_{confrimed_num}" in actions_requested:
                            LOG.info('quiting')
                            self.speak("Initiating shutdown. Goodbye.", private=True)

                            time.sleep(5)

                            # import os
                            if not self.server:
                                os.system("shutdown now -h")

                        if f"eraseAllData_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear All")
                            # TODO: Dialog file DM
                            self.speak("Please wait a moment. I am erasing everything I know about you."
                                       " I enjoyed our friendship. I hope to be your friend once again.", private=True)
                            if not self.server:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -a"])
                            else:
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
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -A " + user_dict["username"]])
                                if message.context["mobile"]:
                                    self.socket_io_emit('clear_data', "&kind=all", message.context["flac_filename"])
                                else:
                                    self.socket_io_emit(event="clear cookies intent",
                                                        flac_filename=message.context["flac_filename"])

                            # Neon.clear_data(['a'])

                        if f"eraseSelectedTranscriptions_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear Selected Transcripts")
                            if f"eraseLikes_{confrimed_num}" in actions_requested:
                                self.speak("Resetting your likes", private=True)
                                if self.server:
                                    user_dict['ignored_brands'] = {}
                                    user_dict['favorite_brands'] = {}
                                    user_dict['specially_requested'] = {}
                                else:
                                    # self.create_signal("NGI_YAML_user_update")
                                    self.user_config.update_yaml_file("brands", "ignored_brands", {}, True)
                                    self.user_config.update_yaml_file("brands", "favorite_brands", {}, True)
                                    self.user_config.update_yaml_file("brands", "specially_requested", {})
                            else:
                                self.speak("Taking care of your selected transcripts folder", private=True)
                            if self.server:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -S " + user_dict["username"]])
                            else:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -s"])

                        if f"eraseIgnoredTranscriptions_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear Ignored Transcripts")
                            if f"eraseIgnoredBrands_{confrimed_num}" in actions_requested:
                                self.speak("Resetting ignored brands.", private=True)
                                if self.server:
                                    user_dict['ignored_brands'] = {}
                                else:
                                    # self.create_signal("NGI_YAML_user_update")
                                    self.user_config.update_yaml_file("brands", "ignored_brands", {})
                            else:
                                self.speak("Taking care of your ignored brands transcriptions", private=True)
                            if self.server:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -I " + user_dict["username"]])
                            else:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -i"])

                        if f"eraseAllTranscriptions_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear All Transcripts")
                            self.speak("Audio recordings and transcriptions cleared", private=True)
                            if self.server:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -T " + user_dict["username"]])
                                if message.context["mobile"]:
                                    self.socket_io_emit('clear_data', "&kind=transcripts",
                                                        message.context["flac_filename"])
                            else:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -t"])

                        if f"eraseProfile_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear Profile")
                            self.speak("Clearing your personal profile data.", private=True)
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
                                # Neon.clear_data(['u'])
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -u"])
                                # TODO: Check This

                        if f"eraseCache_{confrimed_num}" in actions_requested:
                            # Neon.clear_data(['c'])
                            if not self.server:
                                self.speak("Clearing All cached responses.", private=True)
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -c"])
                            else:
                                LOG.debug("Clear Caches")
                                if message.context["mobile"]:
                                    self.socket_io_emit('clear_data', "&kind=cache", message.context["flac_filename"])
                                else:
                                    self.socket_io_emit(event="clear cookies intent",
                                                        kind=message.context["flac_filename"])

                        if f"erasePrefs_{confrimed_num}" in actions_requested:
                            LOG.info(">>> Clear Preferences")
                            # Neon.clear_data(['r'])
                            if self.server:
                                user_dict["lat"] = 47.4799078
                                user_dict["lng"] = -122.2034496
                                user_dict["city"] = "Renton"
                                user_dict["state"] = "Washington"
                                user_dict["country"] = "America/Los_Angeles"
                                user_dict["time"] = 12
                                user_dict["date"] = "MDY"
                                user_dict["measure"] = "imperial"
                            else:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -r"])
                                # TODO: Check This
                            self.speak("Resetting all interface preferences.", private=True)

                        if f"eraseMedia_{confrimed_num}" in actions_requested:
                            # Neon.clear_data(['p'])
                            if self.server:
                                if message.context["mobile"]:
                                    self.socket_io_emit('clear_data', "&kind=media", message.context["flac_filename"])
                                else:
                                    pass
                            else:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -p"])

                            self.speak("Erasing all pictures, videos, and audio recordings I have taken.", private=True)

                        if f"eraseLanguages_{confrimed_num}" in actions_requested:
                            self.speak("Resetting your language preferences.", private=True)
                            # Neon.clear_data(['l'])
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
                            else:
                                subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
                                                 + "/functions.sh; refreshNeon -l"])

                        LOG.debug("DM: Clear Data Confirmed")
                        if self.server:
                            flac_filename = message.context["flac_filename"]
                            self.socket_io_emit(event="update profile", kind="skill",
                                                flac_filename=flac_filename, message=user_dict)
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

# @staticmethod
# def handle_intent_overwrite():
#     # LOG.info(NGI_ROOT_PATH)
#     self.check_for_signal("Intent_overwrite_req")
#     subprocess.Popen(NGI_ROOT_PATH + "/utilities/skip_ww_default.sh", shell=True)
#     self.create_signal("Intent_overwritten")
#     # LOG.info("Intent_overwritten")
#     def handle_random_numeric(self, message):
#         # from NGI.utilities.utilHelper import NeonHelpers as Neon
#         self.check_for_signal(str(self.confirm_number))
#         # string_net = "".join(message.data.get("random_number", None).split()).replace(":", "")
#         confirmation_number = str(message.data.get("utterance")).replace(message.data.get("ConfirmKeyword"), "")
#         # LOG.info(self.confirm_number)
#         LOG.info(f"*****************{str(confirmation_number)} {str(self.confirm_number)}")
#         prefix = "DCC"
#         user_dict = None
#         flac_filename = message.context["flac_filename"]
#
#         if self.server:
#             user_dict = self.build_user_dict(message)
#             # Check for the user-specific signal if server
#             if self.check_for_signal(f"{user_dict['username']}_DCC_{self.confirm_number}"):
#                 LOG.info("DM: Username confirmed")
#                 proceed = True
#                 prefix = f"{user_dict['username']}_DCC"
#             else:
#                 LOG.info("DM: Username not confirmed")
#                 proceed = False
#         else:
#             # Use the numbers in the signal to confirm for non-server users
#             # proceed = int(string_net) == int(self.confirm_number)
#             proceed = str(confirmation_number).__contains__(str(self.confirm_number))
#
#         if proceed:
#             if self.check_for_signal(f"{prefix}_exitNow"):
#                 self.speak("Hope to see you again soon. Goodbye.", private=True)
#                 time.sleep(3)
#                 if not self.server:
#                     subprocess.call([self.configuration_available["dirVars"]["coreDir"] + '/stop_neon.sh'])
#
#             if self.check_for_signal(f"{prefix}_shutdownNow"):
#                 LOG.info('quiting')
#                 self.speak("Initiating shutdown. Goodbye.", private=True)
#
#                 time.sleep(5)
#
#                 # import os
#                 if not self.server:
#                     os.system("shutdown now -h")
#
#             if self.check_for_signal(f"{prefix}_eraseAllData"):
#                 LOG.info(">>> Clear All")
#                 self.speak("Please wait a moment. I am erasing everything I know about you. I enjoyed our friendship."
#                            "I hope to be your friend once again.", private=True)
#                 # import os
#                 # os.chdir(self.configuration_available["dirVars"]["ngiDir"])
#                 if not self.server:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -a"])
#                 else:
#                     user_dict['ignored_brands'] = {}
#                     user_dict['favorite_brands'] = {}
#                     user_dict['specially_requested'] = {}
#                     user_dict['first_name'] = ""
#                     user_dict["middle_name"] = ""
#                     user_dict["last_name"] = ""
#                     user_dict["dob"] = "YYYY/MM/DD"
#                     user_dict["age"] = ""
#                     user_dict["email"] = ""
#                     user_dict["picture"] = ""
#                     user_dict["about"] = ""
#                     user_dict["lat"] = 47.4799078
#                     user_dict["lng"] = -122.2034496
#                     user_dict["city"] = "Renton"
#                     user_dict["state"] = "Washington"
#                     user_dict["country"] = "America/Los_Angeles"
#                     user_dict["time"] = 12
#                     user_dict["date"] = "MDY"
#                     user_dict["measure"] = "imperial"
#                     user_dict["stt_language"] = "en"
#                     user_dict["stt_region"] = "US"
#                     user_dict["alt_languages"] = ['en']
#                     user_dict["tts_language"] = "en-us"
#                     user_dict["tts_gender"] = "female"
#                     user_dict["neon_voice"] = "Joanna"
#                     user_dict["secondary_tts_language"] = ""
#                     user_dict["secondary_tts_gender"] = ""
#                     user_dict["secondary_neon_voice"] = ""
#                     user_dict["speed_multiplier"] = 1.0
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -A " + user_dict["username"]])
#                     if message.context["mobile"]:
#                         self.socket_io_emit('clear_data', "&kind=all", message.context["flac_filename"])
#                     else:
#                         self.socket_io_emit(event="clear cookies intent",
#                                             flac_filename=message.context["flac_filename"])
#
#                 # Neon.clear_data(['a'])
#
#             if self.check_for_signal(f"{prefix}_eraseSelectedTranscriptions"):
#                 LOG.info(">>> Clear Selected Transcripts")
#                 if self.check_for_signal(f"{prefix}_eraseLikes"):
#                     self.speak("Resetting your likes", private=True)
#                     if self.server:
#                         user_dict['ignored_brands'] = {}
#                         user_dict['favorite_brands'] = {}
#                         user_dict['specially_requested'] = {}
#                     else:
#                         # self.create_signal("NGI_YAML_user_update")
#                         self.user_config.update_yaml_file("brands", "ignored_brands", {}, True)
#                         self.user_config.update_yaml_file("brands", "favorite_brands", {}, True)
#                         self.user_config.update_yaml_file("brands", "specially_requested", {})
#                 else:
#                     self.speak("Taking care of your selected transcripts folder", private=True)
#                 if self.server:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -S " + user_dict["username"]])
#                 else:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                     + "/functions.sh; refreshNeon -s"])
#
#             if self.check_for_signal(f"{prefix}_eraseIgnoredTranscriptions"):
#                 LOG.info(">>> Clear Ignored Transcripts")
#                 if self.check_for_signal(f"{prefix}_eraseIgnoredBrands"):
#                     self.speak("Resetting ignored brands.", private=True)
#                     if self.server:
#                         user_dict['ignored_brands'] = {}
#                     else:
#                         # self.create_signal("NGI_YAML_user_update")
#                         self.user_config.update_yaml_file("brands", "ignored_brands", {})
#                 else:
#                     self.speak("Taking care of your ignored brands transcriptions", private=True)
#                 if self.server:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -I " + user_dict["username"]])
#                 else:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                     + "/functions.sh; refreshNeon -i"])
#
#             if self.check_for_signal(f"{prefix}_eraseAllTranscriptions"):
#                 LOG.info(">>> Clear All Transcripts")
#                 self.speak("Audio recordings and transcriptions cleared", private=True)
#                 if self.server:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -T " + user_dict["username"]])
#                     if message.context["mobile"]:
#                         self.socket_io_emit('clear_data', "&kind=transcripts", message.context["flac_filename"])
#                 else:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -t"])
#
#             if self.check_for_signal(f"{prefix}_eraseProfile"):
#                 LOG.info(">>> Clear Profile")
#                 self.speak("Clearing your personal profile data.", private=True)
#                 if self.server:
#                     user_dict['first_name'] = ""
#                     user_dict["middle_name"] = ""
#                     user_dict["last_name"] = ""
#                     user_dict["dob"] = "YYYY/MM/DD"
#                     user_dict["age"] = ""
#                     user_dict["email"] = ""
#                     user_dict["picture"] = ""
#                     user_dict["about"] = ""
#                 else:
#                     # Neon.clear_data(['u'])
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -u"])
#
#             if self.check_for_signal(f"{prefix}_eraseCache"):
#                 # Neon.clear_data(['c'])
#                 if not self.server:
#                     self.speak("Clearing All cached responses.", private=True)
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -c"])
#                 else:
#                     LOG.debug("Clear Caches")
#                     if message.context["mobile"]:
#                         self.socket_io_emit('clear_data', "&kind=cache", message.context["flac_filename"])
#                     else:
#                         self.socket_io_emit(event="clear cookies intent", kind=message.context["flac_filename"])
#
#             if self.check_for_signal(f"{prefix}_erasePrefs"):
#                 LOG.info(">>> Clear Preferences")
#                 # Neon.clear_data(['r'])
#                 if self.server:
#                     user_dict["lat"] = 47.4799078
#                     user_dict["lng"] = -122.2034496
#                     user_dict["city"] = "Renton"
#                     user_dict["state"] = "Washington"
#                     user_dict["country"] = "America/Los_Angeles"
#                     user_dict["time"] = 12
#                     user_dict["date"] = "MDY"
#                     user_dict["measure"] = "imperial"
#                 else:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -r"])
#                 self.speak("Resetting all interface preferences.", private=True)
#
#             if self.check_for_signal(f"{prefix}_eraseMedia"):
#                 # Neon.clear_data(['p'])
#                 if self.server:
#                     if message.context["mobile"]:
#                         self.socket_io_emit('clear_data', "&kind=media", message.context["flac_filename"])
#                     else:
#                         pass
#                 else:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -p"])
#
#                 self.speak("Erasing all pictures, videos, and audio recordings I have taken.", private=True)
#
#             if self.check_for_signal(f"{prefix}_eraseLanguages"):
#                 self.speak("Resetting your language preferences.", private=True)
#                 # Neon.clear_data(['l'])
#                 if self.server:
#                     user_dict["stt_language"] = "en"
#                     user_dict["stt_region"] = "US"
#                     user_dict["alt_languages"] = ['en']
#                     user_dict["tts_language"] = "en-us"
#                     user_dict["tts_gender"] = "female"
#                     user_dict["neon_voice"] = "Joanna"
#                     user_dict["secondary_tts_language"] = ""
#                     user_dict["secondary_tts_gender"] = ""
#                     user_dict["secondary_neon_voice"] = ""
#                     user_dict["speed_multiplier"] = 1.0
#                 else:
#                     subprocess.call(['bash', '-c', ". " + self.configuration_available["dirVars"]["ngiDir"]
#                                      + "/functions.sh; refreshNeon -l"])
#             if self.server:
#                 more_waiting = False
#                 for signal in os.listdir(self.configuration_available['dirVars']['ipcDir'] + '/signal'):
#                     if "DCC" in str(signal):
#                         more_waiting = True
#                         break
#                 if not more_waiting:
#                     self.disable_intent("confirm_numeric_intent")
#                     # self.disable_intent("confirm_numeric.intent")
#             else:
#                 self.disable_intent("confirm_numeric_intent")
#                 # self.disable_intent("confirm_numeric.intent")
#             LOG.debug("DM: Clear Data Confirmed")
#             if self.server:
#                 self.socket_io_emit(event="update profile", kind="skill",
#                                     flac_filename=flac_filename, message=user_dict)
#             else:
#                 self.bus.emit(Message('check.yml.updates',
#                                       {"modified": ["ngi_local_conf", "ngi_user_info"]},
#                                       {"origin": "device-control-center.neon"}))
#             # LOG.debug(data_toggles)
#             # Clear.clear_data(data_toggles)
#             # self.disable_intent("not_now_intent")
#         else:
#             self.speak("Please try again. The action was not confirmed", private=True)
#
#     def handle_confirm_yes(self, message):
#         self.check_for_signal(str(self.confirm_number))
#         self.disable_intent('confirm_yes')
#         self.disable_intent('confirm_no')
#
#         if self.check_for_signal("DCC_StartSWWResponse", 0):
#             # import os
#             from NGI.utilities.utilHelper import NeonHelpers
#             # self.create_signal('skip_wake_word')
#             # self.create_signal('restartedFromSkill')
#             # self.create_signal("Intent_overwrite_req")
#             # self.handle_intent_overwrite()
#             self.speak("Okay, starting to skip wake words.", False, private=True)
#             time.sleep(1)
#             NeonHelpers.disable_ww()
#             # os.system("sudo -H -u " + self.configuration_available['devVars']['installUser'] + ' ' +
#             #           NGI_ROOT_PATH + "/utilities/skip_ww_default.sh")
#             # os.system("sudo -H -u " + self.configuration_available['devVars']['installUser'] + ' ' +
#             #           self.configuration_available['dirVars']['coreDir'] + "/start_neon.sh voice")
#             # time.sleep(2)
#             # os.system("sudo -H -u " + self.configuration_available['devVars']['installUser'] + ' ' +
#             #           self.configuration_available['dirVars']['coreDir'] + "/start_neon.sh skills")
#             # time.sleep(3)
#             # pid = os.fork()
#             # if pid == 0:
#             #     subprocess.call(
#             #         ['gnome-terminal', '--', self.configuration_available["dirVars"]["ngiDir"] + "/run.sh"])
#
#         if self.check_for_signal("DCC_startDemoPrompt"):
#             self.handle_show_demo(message)
#
#         if self.check_for_signal("DCC_demoNextTime"):
#             self.speak("Understood.", private=True)
#
#         if self.check_for_signal("DCC_StopSkippingWW", 0):
#             # import os
#             from NGI.utilities.utilHelper import NeonHelpers
#             # self.check_for_signal("Intent_overwrite_req")
#             # self.check_for_signal('skip_wake_word')
#             # LOG.info("Intents cleared to default")
#             # self.create_signal('restartedFromSkill')
#             self.speak("Okay, entering wake words mode.", False, private=True)
#             time.sleep(1)
#             NeonHelpers.enable_ww()
#             # os.system("sudo -H -u " + self.configuration_available['devVars']['installUser'] + ' ' +
#             #           NGI_ROOT_PATH + "/utilities/ww_default.sh")
#             #
#             # os.system("sudo -H -u " + self.configuration_available['devVars']['installUser'] + ' ' +
#             #           self.configuration_available['dirVars']['coreDir'] + "/start_neon.sh voice")
#             # time.sleep(2)
#             # os.system("sudo -H -u " + self.configuration_available['devVars']['installUser'] + ' ' +
#             #           self.configuration_available['dirVars']['coreDir'] + "/start_neon.sh skills")
#
#             # time.sleep(5)
#             # pid = os.fork()
#             # if pid == 0:
#             #     subprocess.call(
#             #         ['gnome-terminal', '--', self.configuration_available["dirVars"]["ngiDir"] + "/run.sh"])
#
#         if self.check_for_signal("DCC_StartRandomResponse", 0):
#             if not self.check_for_signal("use_default_response", -1):
#                 self.speak("I am already using my random responses", private=True)
#             else:
#                 self.check_for_signal("use_default_response")
#                 self.speak("No problem. I will use my dialog options from now on", private=True)
#
#         if self.check_for_signal("DCC_StartDefaultResponse", 0):
#             if not self.check_for_signal("use_default_response", -1):
#                 self.create_signal("use_default_response")
#                 self.speak("Understood. I will use my primary responses to answer your requests.", private=True)
#             else:
#                 self.speak("I am already using my primary responses. Try asking me something else.", private=True)
#
#         if self.check_for_signal("DCC_initiateUpdate", -1):
#             if not self.server:
#                 self.speak("Starting the update.", private=True)
#                 try:
#                     # import os
#                     os.chdir(self.configuration_available["dirVars"]["ngiDir"])
#                     # self.create_signal("update_from_skill")
#                     subprocess.call(['gnome-terminal', '--', 'sudo', "./update.sh"])
#                     # self.speak("Updates complete. I may need to restart. Please stay with me")
#                     # self.emitter.emit(Message('configuration.updated'))
#
#                 except HTTPError as e:
#                     LOG.info(e)
#         self.stop()
#
#     def handle_confirm_no(self, message):
#         LOG.info(message)
#         self.disable_intent('confirm_yes')
#         self.disable_intent('confirm_no')
#         self.check_for_signal(str(self.confirm_number))
#
#         if self.check_for_signal("DCC_demoNextTime"):
#             self.speak("If you want to see the demo in the future, say \"Neon, show me the demo\".", private=True)
#             # self.configuration_available["devVars"]["showDemo"] = False
#             self.local_config.update_yaml_file("prefFlags", "showDemo", False, final=True)
#
#         elif self.check_for_signal("DCC_shutdownNow") or self.check_for_signal("DCC_exitNow") or \
#                 self.check_for_signal("DCC_eraseAllData"):
#             self.speak("Glad to stay with you", private=True)
#
#         elif self.check_for_signal("DCC_startDemoPrompt"):
#             self.create_signal("DCC_demoNextTime")
#             self.speak("Should I ask you next time?", True, private=True)
#             self.enable_intent('confirm_yes')
#             self.enable_intent('confirm_no')
#
#         else:  # No follow-up questions
#             self.speak("Okay. Not doing anything.", False, private=True)
#             # self.check_for_signal("DCC_eraseIgnoredBrands")
#             # self.check_for_signal("DCC_eraseIgnoredTranscriptions")
#             # self.check_for_signal("DCC_StartRandomResponse", 0)
#             # self.check_for_signal("DCC_StartDefaultResponse", 0)
#             # self.check_for_signal("DCC_StopSkippingWW", 0)
#             # self.check_for_signal("DCC_initiateUpdate")
#             # self.check_for_signal("DCC_StartSWWResponse")
#             # self.check_for_signal("DCC_demoNextTime")
#             # self.check_for_signal("DCC_eraseSelectedTranscriptions")
#             # self.check_for_signal("DCC_eraseLikes")
#             # self.check_for_signal("DCC_eraseSelectedTranscriptions")
#             self.disable_intent('confirm_numeric_intent')
#             # self.disable_intent('confirm_numeric.intent')
#             self.stop()  # This clears signals
