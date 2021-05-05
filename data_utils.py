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

from glob import glob
from shutil import rmtree
from neon_utils.configuration_utils import get_neon_local_config, get_neon_device_type
from neon_utils.logger import LOG

LOCAL_CONF = get_neon_local_config()
ALL_TRANSCRIPTS = ("ts_transcripts", "ts_selected_transcripts", "ts_ignored_transcripts",
                   "ts_transcript_audio_segments")
ALL_MEDIA = ("music", "video", "pictures")


# TODO: Add unit tests for these! DM
def refresh_neon(data_to_remove: str, user: str):
    if data_to_remove == "all":
        remove_transcripts(ALL_TRANSCRIPTS, user)
        remove_media(ALL_MEDIA, user)
    elif data_to_remove == "ignored":
        remove_transcripts(tuple("ts_ignored_transcripts"), user)
    elif data_to_remove == "selected":
        remove_transcripts(tuple("ts_selected_transcripts"), user)
    elif data_to_remove == "brands":
        remove_transcripts(("ts_selected_transcripts", "ts_ignored_transcripts"), user)
    elif data_to_remove == "transcripts":
        remove_transcripts(ALL_TRANSCRIPTS, user)
    elif data_to_remove == "media":
        remove_media(ALL_MEDIA, user)
    elif data_to_remove == "caches":
        remove_cache(user)
    else:
        LOG.warning(f"Unknown data type: {data_to_remove}")


def remove_transcripts(directories: tuple, user: str):
    docs_dir = os.path.expanduser(LOCAL_CONF["dirVars"].get("docsDir", "~/Documents/NeonGecko"))
    for directory in directories:
        transcript_path = os.path.join(docs_dir, directory)
        if get_neon_device_type() == "server":
            user_transcripts = glob(os.path.join(transcript_path, f"{user}-*"))
            for transcript in user_transcripts:
                rmtree(transcript)
        else:
            rmtree(transcript_path)


def remove_media(media: tuple, user: str):
    media_locations = {"music": LOCAL_CONF["dirVars"]["musicDir"],
                       "pictures": LOCAL_CONF["dirVars"]["picsDir"],
                       "video": LOCAL_CONF["dirVars"]["videoDir"]}
    for kind in media:
        dir_to_clean = media_locations.get(kind)
        if dir_to_clean:
            if get_neon_device_type() == "server":
                # TODO: Remove media indexed by username
                pass
            else:
                rmtree(dir_to_clean)


def remove_cache(user):
    if get_neon_device_type() == "server" and user != "admin":
        LOG.warning(f"{user} not allowed to clear cache!")
        return
    if LOCAL_CONF["dirVars"].get("cacheDir"):
        rmtree(LOCAL_CONF["dirVars"]["cacheDir"])
